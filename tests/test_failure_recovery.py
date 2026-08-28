from __future__ import annotations

import sqlite3
import threading
from datetime import date
from decimal import Decimal

import pytest

from recovery_radar.auth import Principal
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.recovery import (
    BackupVerificationError,
    backup_verified,
    database_truth_digest,
    verify_database_path,
)
from recovery_radar.service import TenantService
from recovery_radar.storage import Storage
from recovery_radar.synthetic import alpha_components_fixture


def _principal(role="ANALYST"):
    return Principal("A", role.lower(), role)


def _event(event_id="EV-INTERRUPT"):
    return alpha_components_fixture()[0].__class__(
        event_id,
        "OEM-A",
        "PRG-A",
        "PART-A",
        "PROGRAM_CANCELLED",
        date(2026, 7, 1),
        Decimal("100"),
        Decimal("0"),
        f"event://{event_id}",
        f"notice://{event_id}",
    )


def _seed_claimable_gateway(path):
    store = Storage(path)
    store.create_workspace("A", "Supplier A")
    gateway = RecoveryRadarGateway(store)
    admin = gateway.bootstrap_workspace_admin("A", "admin")
    analyst = gateway.issue_key(admin, "analyst", "ANALYST")
    reviewer = gateway.issue_key(admin, "reviewer", "REVIEWER")
    event, exposures, entitlements, _ = alpha_components_fixture()
    gateway.store_recovery_event(analyst, event)
    for exposure in exposures:
        gateway.store_exposure_line(analyst, exposure)
    for entitlement in entitlements:
        gateway.store_entitlement_basis(analyst, entitlement)
        gateway.review_entitlement_basis(
            reviewer, entitlement.entitlement_id, "VERIFIED", "fixture checked"
        )
    documents = (
        ("D-N", "CUSTOMER_NOTICE", "document://alpha/customer-notice", None),
        ("D-I", "INVENTORY_RECORD", "inventory://alpha/A1", None),
        ("D-C", "CONTRACT", "contract://alpha/termination-clause", True),
        ("D-P", "PURCHASE_ORDER", "po://alpha/PO-1", None),
        ("D-M", "MITIGATION_RECORD", "mitigation://alpha/resale", None),
    )
    for document_id, evidence_type, source_ref, signed in documents:
        document = EvidenceDocument.from_bytes(
            document_id=document_id,
            workspace_id="A",
            supplier_id="SUP-A",
            customer_id="OEM-A",
            program_id="PRG-A",
            evidence_type=evidence_type,
            source_ref=source_ref,
            version_id="v1",
            document_date=date(2026, 5, 1),
            content=f"{document_id}:{source_ref}".encode(),
            signed=signed,
        )
        gateway.store_evidence_document(analyst, document)
        gateway.review_evidence_document(
            reviewer, document_id, "VERIFIED", "fixture checked"
        )
    case = gateway.create_case(analyst, event.event_id, "SUP-A")
    return store, gateway, admin, analyst, reviewer, case


def test_interrupted_source_write_rolls_back_un_audited_event(tmp_path):
    store = Storage(tmp_path / "interrupt.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        store.conn.execute(
            """
            CREATE TRIGGER reject_event_audit
            BEFORE INSERT ON audit_events
            WHEN NEW.entity_type='RECOVERY_EVENT'
            BEGIN
              SELECT RAISE(ABORT, 'forced audit failure');
            END;
            """
        )
        store.conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="forced audit failure"):
            service.store_recovery_event(_principal(), _event())
        assert service.get_recovery_event(_principal(), "EV-INTERRUPT") is None
        assert store.conn.in_transaction is False
    finally:
        store.close()


def test_interrupted_review_write_rolls_back_verification(tmp_path):
    store = Storage(tmp_path / "review-interrupt.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        analyst = _principal("ANALYST")
        reviewer = _principal("REVIEWER")
        document = EvidenceDocument.from_bytes(
            document_id="DOC-1",
            workspace_id="A",
            supplier_id="SUP-A",
            customer_id="OEM-A",
            program_id="PRG-A",
            evidence_type="CONTRACT",
            source_ref="contract://1",
            version_id="v1",
            document_date=date(2026, 1, 1),
            content=b"contract",
            signed=True,
        )
        service.store_evidence_document(analyst, document)
        store.conn.execute(
            """
            CREATE TRIGGER reject_review_audit
            BEFORE INSERT ON audit_events
            WHEN NEW.entity_type='EVIDENCE_REVIEW'
            BEGIN
              SELECT RAISE(ABORT, 'forced review audit failure');
            END;
            """
        )
        store.conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="forced review audit failure"):
            service.review_evidence_document(reviewer, "DOC-1", "VERIFIED")
        assert service.evidence_reviews.current_state("A", "DOC-1") is None
        assert store.conn.in_transaction is False
    finally:
        store.close()


def test_interrupted_claim_transition_preserves_previous_state(tmp_path):
    store, gateway, _, analyst, _, case = _seed_claimable_gateway(
        tmp_path / "claim-interrupt.db"
    )
    try:
        assert case.state == "DETECTED"
        store.conn.execute(
            """
            CREATE TRIGGER reject_claim_audit
            BEFORE INSERT ON audit_events
            WHEN NEW.entity_type='CLAIM_CASE'
            BEGIN
              SELECT RAISE(ABORT, 'forced claim audit failure');
            END;
            """
        )
        store.conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="forced claim audit failure"):
            gateway.advance_case(analyst, case.case_id, "ANALYSIS")
        recovered = gateway.get_case(analyst, case.case_id)
        assert recovered.state == "DETECTED"
        assert store.conn.in_transaction is False
    finally:
        store.close()


def test_database_lock_fails_without_partial_event_and_recovers(tmp_path):
    path = tmp_path / "locked.db"
    store = Storage(path)
    blocker = sqlite3.connect(path)
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        store.conn.execute("PRAGMA busy_timeout=25")
        blocker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError):
            service.store_recovery_event(_principal(), _event("EV-LOCK"))
        blocker.rollback()
        assert service.get_recovery_event(_principal(), "EV-LOCK") is None
        service.store_recovery_event(_principal(), _event("EV-LOCK"))
        assert service.get_recovery_event(_principal(), "EV-LOCK") is not None
    finally:
        blocker.close()
        store.close()


def test_verified_backup_matches_full_database_truth_and_detects_corruption(tmp_path):
    path = tmp_path / "source.db"
    backup = tmp_path / "backup.db"
    store, _, _, _, _, _ = _seed_claimable_gateway(path)
    try:
        source_digest = database_truth_digest(store.conn)
        report = backup_verified(store, backup)
        assert report["quick_check"] == "ok"
        assert report["foreign_key_violations"] == 0
        assert report["truth_digest"] == source_digest
    finally:
        store.close()
    assert verify_database_path(backup)["truth_digest"] == source_digest
    backup.write_bytes(b"not-a-sqlite-database")
    with pytest.raises(BackupVerificationError, match="SQLITE_BACKUP_UNREADABLE"):
        verify_database_path(backup)


def test_duplicate_case_request_is_economically_idempotent(tmp_path):
    store, gateway, _, analyst, _, first = _seed_claimable_gateway(
        tmp_path / "duplicate.db"
    )
    try:
        second = gateway.create_case(analyst, "EV-ALPHA-1", "SUP-A")
        assert second.case_id == first.case_id
        assert second.claim_amount == first.claim_amount == Decimal("800.00")
        row_count = store.conn.execute(
            "SELECT COUNT(*) n FROM claim_cases WHERE workspace_id='A' AND case_id=?",
            (first.case_id,),
        ).fetchone()["n"]
        assert row_count == 1
    finally:
        store.close()


def test_concurrent_submission_cannot_create_duplicate_claim_rows(tmp_path):
    path = tmp_path / "concurrent.db"
    store, gateway, _, analyst, _, case = _seed_claimable_gateway(path)
    for state in ("ANALYSIS", "REVIEW", "CLAIM_READY"):
        gateway.advance_case(analyst, case.case_id, state)
    store.close()

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def submit_once():
        local = Storage(path)
        try:
            local_gateway = RecoveryRadarGateway(local)
            barrier.wait()
            try:
                updated = local_gateway.advance_case(
                    analyst, case.case_id, "SUBMITTED"
                )
                outcome = updated.state
            except (ValueError, sqlite3.OperationalError) as exc:
                outcome = type(exc).__name__
            with lock:
                outcomes.append(outcome)
        finally:
            local.close()

    threads = [threading.Thread(target=submit_once) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final_store = Storage(path)
    try:
        final = final_store.get_claim_case("A", case.case_id)
        assert final.state == "SUBMITTED"
        assert final_store.conn.execute(
            "SELECT COUNT(*) n FROM claim_cases WHERE workspace_id='A' AND case_id=?",
            (case.case_id,),
        ).fetchone()["n"] == 1
        assert len(outcomes) == 2
        assert any(outcome == "SUBMITTED" for outcome in outcomes)
    finally:
        final_store.close()
