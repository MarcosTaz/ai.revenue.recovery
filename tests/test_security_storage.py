from decimal import Decimal

import pytest

from recovery_radar.auth import Principal
from recovery_radar.service import TenantService
from recovery_radar.storage import Storage
from recovery_radar.workflow import ClaimCase, PaymentRecord


def p(workspace, actor, role="ADMIN"):
    return Principal(workspace, actor, role)


def test_same_case_id_is_isolated_between_tenants(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        service.create_case(p("A", "alice"), ClaimCase("CASE-1", "A", Decimal("100"), "EUR"))
        service.create_case(p("B", "bob"), ClaimCase("CASE-1", "B", Decimal("999"), "USD"))
        assert service.get_case(p("A", "alice"), "CASE-1").claim_amount == Decimal("100")
        assert service.get_case(p("B", "bob"), "CASE-1").claim_amount == Decimal("999")
    finally:
        store.close()


def test_cross_tenant_case_injection_is_rejected(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        with pytest.raises(PermissionError, match="CROSS_TENANT"):
            service.create_case(p("A", "alice"), ClaimCase("CASE-X", "B", Decimal("100"), "EUR"))
        assert service.get_case(p("A", "alice"), "CASE-X") is None
    finally:
        store.close()


def test_guessed_foreign_case_id_returns_none_not_foreign_data(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        service.create_case(p("B", "bob"), ClaimCase("SECRET-CASE", "B", Decimal("999"), "EUR"))
        assert service.get_case(p("A", "alice"), "SECRET-CASE") is None
    finally:
        store.close()


def test_reviewer_cannot_create_case_or_record_payment(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        reviewer = p("A", "reviewer", "REVIEWER")
        admin = p("A", "admin")
        with pytest.raises(PermissionError, match="CASE_CREATE"):
            service.create_case(reviewer, ClaimCase("CASE-X", "A", Decimal("100"), "EUR"))
        service.create_case(admin, ClaimCase("CASE-1", "A", Decimal("100"), "EUR"))
        for state in ("ANALYSIS", "REVIEW", "CLAIM_READY", "SUBMITTED"):
            service.advance_case(reviewer, "CASE-1", state)
        service.advance_case(
            reviewer,
            "CASE-1",
            "SETTLED",
            settled_amount=Decimal("80"),
            settlement_evidence_ref="settlement://1",
        )
        with pytest.raises(PermissionError, match="PAYMENT"):
            service.record_payment(
                reviewer,
                "CASE-1",
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
    service.create_case(admin, ClaimCase("CASE-1", "A", Decimal("100"), "EUR"))
    for state in ("ANALYSIS", "REVIEW", "CLAIM_READY", "SUBMITTED"):
        service.advance_case(admin, "CASE-1", state)
    service.advance_case(
        admin,
        "CASE-1",
        "SETTLED",
        settled_amount=Decimal("80"),
        settlement_evidence_ref="settlement://1",
    )
    service.record_payment(
        admin,
        "CASE-1",
        PaymentRecord("P1", Decimal("50"), "EUR", "bank://P1"),
    )
    before = store.economic_digest("A")
    store.backup_to(backup)
    store.close()
    restored = Storage(backup)
    try:
        assert restored.economic_digest("A") == before
        case = restored.get_claim_case("A", "CASE-1")
        assert case.state == "PAYMENT_PENDING"
        assert case.settled_amount == Decimal("80")
        assert case.paid_amount == Decimal("50")
    finally:
        restored.close()
