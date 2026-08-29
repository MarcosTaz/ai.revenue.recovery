from datetime import date
from decimal import Decimal

import pytest

from recovery_radar.evidence import EvidenceDocument
from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.models import EntitlementBasis, RecoveryEvent
from recovery_radar.storage import Storage


def _event():
    return RecoveryEvent(
        "EV-1",
        "OEM-A",
        "PRG-A",
        "PART-A",
        "PROGRAM_CANCELLED",
        date(2026, 7, 1),
        Decimal("100"),
        Decimal("0"),
        "event://1",
        "notice://1",
    )


def _document():
    return EvidenceDocument.from_bytes(
        document_id="D-1",
        workspace_id="A",
        supplier_id="SUP-A",
        customer_id="OEM-A",
        program_id="PRG-A",
        evidence_type="CONTRACT",
        source_ref="contract://1",
        version_id="v1",
        document_date=date(2026, 1, 1),
        content=b"contract evidence",
        signed=True,
    )


def _basis():
    return EntitlementBasis(
        "ENT-1",
        "EV-1",
        "LOSS-1",
        "SUPPORTED",
        "contract://1",
        "po://1",
    )


def test_reviewer_cannot_upload_evidence_then_verify_it(tmp_path):
    store = Storage(tmp_path / "review.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "owner")
        reviewer = gateway.issue_key(admin, "reviewer", "REVIEWER")
        with pytest.raises(PermissionError, match="SOURCE_WRITE"):
            gateway.store_evidence_document(reviewer, _document())
    finally:
        store.close()


def test_same_actor_cannot_create_and_independently_verify_evidence_or_entitlement(tmp_path):
    store = Storage(tmp_path / "review.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "owner")
        analyst_same_actor = gateway.issue_key(admin, "sam", "ANALYST")
        reviewer_same_actor = gateway.issue_key(admin, "sam", "REVIEWER")

        gateway.store_recovery_event(analyst_same_actor, _event())
        gateway.store_entitlement_basis(analyst_same_actor, _basis())
        gateway.store_evidence_document(analyst_same_actor, _document())

        with pytest.raises(PermissionError, match="SELF_REVIEW_NOT_ALLOWED"):
            gateway.review_entitlement_basis(
                reviewer_same_actor, "ENT-1", "VERIFIED"
            )
        with pytest.raises(PermissionError, match="SELF_REVIEW_NOT_ALLOWED"):
            gateway.review_evidence_document(
                reviewer_same_actor, "D-1", "VERIFIED"
            )
    finally:
        store.close()


def test_distinct_reviewer_actor_can_verify_source_records(tmp_path):
    store = Storage(tmp_path / "review.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "owner")
        analyst = gateway.issue_key(admin, "analyst", "ANALYST")
        reviewer = gateway.issue_key(admin, "reviewer", "REVIEWER")

        gateway.store_recovery_event(analyst, _event())
        gateway.store_entitlement_basis(analyst, _basis())
        gateway.store_evidence_document(analyst, _document())
        gateway.review_entitlement_basis(reviewer, "ENT-1", "VERIFIED")
        gateway.review_evidence_document(reviewer, "D-1", "VERIFIED")

        assert gateway.tenant.entitlement_reviews.current_state("A", "ENT-1") == "VERIFIED"
        assert gateway.tenant.evidence_reviews.current_state("A", "D-1") == "VERIFIED"
    finally:
        store.close()
