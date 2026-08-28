from datetime import date
from decimal import Decimal

import pytest

from recovery_radar.auth import Principal
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.models import EntitlementBasis, ExposureLine, RecoveryEvent
from recovery_radar.service import TenantService
from recovery_radar.storage import Storage
from recovery_radar.workflow import PaymentRecord


def p(workspace, actor, role="ADMIN"):
    return Principal(workspace, actor, role)


def seed_sources(service, principal, supplier_id, *, amount="100"):
    event = RecoveryEvent(
        "EV-1",
        "OEM-1",
        "PRG-1",
        "PART-1",
        "PROGRAM_CANCELLED",
        date(2026, 7, 1),
        Decimal("1000"),
        Decimal("0"),
        "event://EV-1",
        "document://notice",
    )
    exposure = ExposureLine(
        "EXP-1",
        "EV-1",
        "LOSS-1",
        "RAW_MATERIAL",
        Decimal(amount) / Decimal("10"),
        Decimal("10"),
        "EUR",
        "inventory://EXP-1",
        "SUPPLIER",
    )
    entitlement = EntitlementBasis(
        "ENT-1",
        "EV-1",
        "LOSS-1",
        "SUPPORTED",
        "contract://termination",
        "po://PO-1",
    )
    service.store_recovery_event(principal, event)
    service.store_exposure_line(principal, exposure)
    service.store_entitlement_basis(principal, entitlement)
    docs = (
        ("D-NOTICE", "CUSTOMER_NOTICE", "document://notice", None),
        ("D-INV", "INVENTORY_RECORD", "inventory://EXP-1", None),
        ("D-CONTRACT", "CONTRACT", "contract://termination", True),
        ("D-PO", "PURCHASE_ORDER", "po://PO-1", None),
    )
    for document_id, evidence_type, source_ref, signed in docs:
        service.store_evidence_document(
            principal,
            EvidenceDocument.from_bytes(
                document_id=document_id,
                workspace_id=principal.workspace_id,
                supplier_id=supplier_id,
                customer_id="OEM-1",
                program_id="PRG-1",
                evidence_type=evidence_type,
                source_ref=source_ref,
                version_id="v1",
                document_date=date(2026, 7, 1),
                content=f"{principal.workspace_id}:{document_id}:{amount}".encode(),
                signed=signed,
            ),
        )


def seed_claimable_case(service, principal, supplier_id, *, amount="100"):
    seed_sources(service, principal, supplier_id, amount=amount)
    return service.create_case(principal, "EV-1", supplier_id)


def test_derived_claims_are_tenant_isolated_and_foreign_ids_hidden(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        case_a = seed_claimable_case(service, p("A", "alice"), "SUP-A", amount="100")
        case_b = seed_claimable_case(service, p("B", "bob"), "SUP-B", amount="999")
        assert case_a.claim_amount == Decimal("100")
        assert case_b.claim_amount == Decimal("999")
        assert service.get_case(p("A", "alice"), case_b.case_id) is None
        assert service.get_case(p("B", "bob"), case_a.case_id) is None
    finally:
        store.close()


def test_cross_tenant_event_reference_cannot_create_foreign_claim(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        seed_sources(service, p("B", "bob"), "SUP-B")
        with pytest.raises(KeyError, match="RECOVERY_EVENT_NOT_FOUND"):
            service.create_case(p("A", "alice"), "EV-1", "SUP-A")
    finally:
        store.close()


def test_reviewer_can_review_but_cannot_create_submit_settle_or_record_payment(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        reviewer = p("A", "reviewer", "REVIEWER")
        admin = p("A", "admin")
        seed_sources(service, admin, "SUP-A")
        with pytest.raises(PermissionError, match="CASE_CREATE"):
            service.create_case(reviewer, "EV-1", "SUP-A")
        case = service.create_case(admin, "EV-1", "SUP-A")
        for state in ("ANALYSIS", "REVIEW", "CLAIM_READY"):
            service.advance_case(reviewer, case.case_id, state)
        with pytest.raises(PermissionError, match="COMMERCIAL_DISPOSITION"):
            service.advance_case(reviewer, case.case_id, "SUBMITTED")
        service.advance_case(admin, case.case_id, "SUBMITTED")
        with pytest.raises(PermissionError, match="COMMERCIAL_DISPOSITION"):
            service.advance_case(
                reviewer,
                case.case_id,
                "SETTLED",
                settled_amount=Decimal("80"),
                settlement_evidence_ref="settlement://1",
            )
        service.advance_case(
            admin,
            case.case_id,
            "SETTLED",
            settled_amount=Decimal("80"),
            settlement_evidence_ref="settlement://1",
        )
        with pytest.raises(PermissionError, match="PAYMENT"):
            service.record_payment(
                reviewer,
                case.case_id,
                PaymentRecord("P1", Decimal("80"), "EUR", "bank://1"),
            )
    finally:
        store.close()


def test_backup_restore_preserves_claim_payment_truth(tmp_path):
    path = tmp_path / "rr.db"
    backup = tmp_path / "backup.db"
    store = Storage(path)
    store.create_workspace("A", "Supplier A")
    service = TenantService(store)
    admin = p("A", "admin")
    case = seed_claimable_case(service, admin, "SUP-A")
    for state in ("ANALYSIS", "REVIEW", "CLAIM_READY", "SUBMITTED"):
        service.advance_case(admin, case.case_id, state)
    service.advance_case(
        admin,
        case.case_id,
        "SETTLED",
        settled_amount=Decimal("80"),
        settlement_evidence_ref="settlement://1",
    )
    service.record_payment(
        admin,
        case.case_id,
        PaymentRecord("P1", Decimal("50"), "EUR", "bank://P1"),
    )
    before = store.economic_digest("A")
    store.backup_to(backup)
    store.close()
    restored = Storage(backup)
    try:
        assert restored.economic_digest("A") == before
        recovered = restored.get_claim_case("A", case.case_id)
        assert recovered.state == "PAYMENT_PENDING"
        assert recovered.settled_amount == Decimal("80")
        assert recovered.paid_amount == Decimal("50")
        assert recovered.event_id == "EV-1"
        assert recovered.selected_exposure_ids == ("EXP-1",)
    finally:
        restored.close()
