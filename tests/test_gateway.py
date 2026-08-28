from datetime import date
from decimal import Decimal

import pytest

from recovery_radar.evidence import EvidenceDocument
from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.storage import Storage
from recovery_radar.synthetic import alpha_components_fixture


def doc(document_id, source_ref, evidence_type, *, signed=None):
    return EvidenceDocument.from_bytes(
        document_id=document_id,
        workspace_id="A",
        supplier_id="SUP-A",
        customer_id="OEM-A",
        program_id="PRG-A",
        evidence_type=evidence_type,
        source_ref=source_ref,
        version_id="v1",
        document_date=date(2026, 1, 1),
        content=f"{document_id}:{source_ref}".encode(),
        signed=signed,
    )


def seed_alpha(gateway, analyst_token, reviewer_token=None):
    event, exposures, entitlements, _ = alpha_components_fixture()
    gateway.store_recovery_event(analyst_token, event)
    for line in exposures:
        gateway.store_exposure_line(analyst_token, line)
    for basis in entitlements:
        gateway.store_entitlement_basis(analyst_token, basis)
    for item in (
        doc("D-N", "document://alpha/customer-notice", "CUSTOMER_NOTICE"),
        doc("D-I", "inventory://alpha/A1", "INVENTORY_RECORD"),
        doc("D-C", "contract://alpha/termination-clause", "CONTRACT", signed=True),
        doc("D-P", "po://alpha/PO-1", "PURCHASE_ORDER"),
        doc("D-M", "mitigation://alpha/resale", "MITIGATION_RECORD"),
    ):
        gateway.store_evidence_document(analyst_token, item)
        if reviewer_token is not None:
            gateway.review_evidence_document(
                reviewer_token, item.document_id, "VERIFIED", "synthetic reviewed"
            )


def test_gateway_derives_tenant_from_token_for_complete_claim_creation(tmp_path):
    store = Storage(tmp_path / "gateway.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        gateway = RecoveryRadarGateway(store)
        admin_a = gateway.bootstrap_workspace_admin("A", "admin-a")
        admin_b = gateway.bootstrap_workspace_admin("B", "admin-b")
        analyst_a = gateway.issue_key(admin_a, "analyst-a", "ANALYST")
        reviewer_a = gateway.issue_key(admin_a, "reviewer-a", "REVIEWER")
        analyst_b = gateway.issue_key(admin_b, "analyst-b", "ANALYST")
        seed_alpha(gateway, analyst_a, reviewer_a)
        case = gateway.create_case(analyst_a, "EV-ALPHA-1", "SUP-A")
        assert case.claim_amount == Decimal("800.00")
        assert case.workspace_id == "A"
        assert gateway.get_case(analyst_a, case.case_id).case_id == case.case_id
        assert gateway.get_case(analyst_b, case.case_id) is None
    finally:
        store.close()


def test_invalid_token_fails_before_business_read(tmp_path):
    store = Storage(tmp_path / "gateway.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        gateway.bootstrap_workspace_admin("A", "admin-a")
        with pytest.raises(PermissionError, match="INVALID_API_KEY"):
            gateway.get_case("rrk_invalid.invalid", "CASE-X")
    finally:
        store.close()


def test_analyst_cannot_self_verify_uploaded_evidence(tmp_path):
    store = Storage(tmp_path / "gateway.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "admin-a")
        analyst = gateway.issue_key(admin, "analyst-a", "ANALYST")
        seed_alpha(gateway, analyst)
        with pytest.raises(PermissionError, match="REVIEWER_REQUIRED"):
            gateway.review_evidence_document(analyst, "D-C", "VERIFIED")
        analysis = gateway.analyze_event(analyst, "EV-ALPHA-1", "SUP-A")
        assert analysis["claimable_total"] == "0.00"
    finally:
        store.close()


def test_reviewer_token_can_verify_but_cannot_create_source_economics_or_claim(tmp_path):
    store = Storage(tmp_path / "gateway.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "admin-a")
        analyst = gateway.issue_key(admin, "analyst-a", "ANALYST")
        reviewer = gateway.issue_key(admin, "reviewer-a", "REVIEWER")
        seed_alpha(gateway, analyst, reviewer)
        event, _, _, _ = alpha_components_fixture()
        with pytest.raises(PermissionError, match="SOURCE_WRITE"):
            gateway.store_recovery_event(reviewer, event)
        with pytest.raises(PermissionError, match="CASE_CREATE"):
            gateway.create_case(reviewer, "EV-ALPHA-1", "SUP-A")
        assert gateway.create_case(analyst, "EV-ALPHA-1", "SUP-A").claim_amount == Decimal("800.00")
    finally:
        store.close()


def test_revoked_token_loses_business_access_immediately(tmp_path):
    store = Storage(tmp_path / "gateway.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "admin-a")
        analyst = gateway.issue_key(admin, "analyst-a", "ANALYST")
        key_id = gateway.auth.key_id_from_token(analyst)
        gateway.revoke_key(admin, key_id)
        with pytest.raises(PermissionError, match="INVALID_API_KEY"):
            gateway.get_case(analyst, "CASE-X")
    finally:
        store.close()
