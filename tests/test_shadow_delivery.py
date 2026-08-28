from datetime import date
from decimal import Decimal

from recovery_radar.evidence import EvidenceDocument
from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.storage import Storage
from recovery_radar.synthetic import alpha_components_fixture


REQUIRED_DELIVERY_SECTIONS = {
    "executive_summary",
    "claim_line_items",
    "exposure_by_category",
    "entitlement_basis",
    "calculation_trace",
    "mitigation",
    "evidence",
    "missing_evidence",
    "uncertainty",
    "recoverability",
    "draft_claim_package",
    "audit_trail",
}


def _document(document_id, source_ref, evidence_type, *, signed=None):
    return EvidenceDocument.from_bytes(
        document_id=document_id,
        workspace_id="SHADOW",
        supplier_id="SUP-ALPHA",
        customer_id="OEM-A",
        program_id="PRG-A",
        evidence_type=evidence_type,
        source_ref=source_ref,
        version_id="v1",
        document_date=date(2026, 5, 1),
        content=f"shadow:{document_id}:{source_ref}".encode(),
        signed=signed,
    )


def _seed_alpha(gateway, token, *, include_contract=True):
    event, exposures, entitlements, _ = alpha_components_fixture()
    gateway.store_recovery_event(token, event)
    for line in exposures:
        gateway.store_exposure_line(token, line)
    for basis in entitlements:
        gateway.store_entitlement_basis(token, basis)
    documents = [
        _document("D-NOTICE", "document://alpha/customer-notice", "CUSTOMER_NOTICE"),
        _document("D-INV", "inventory://alpha/A1", "INVENTORY_RECORD"),
        _document("D-PO", "po://alpha/PO-1", "PURCHASE_ORDER"),
        _document("D-MIT", "mitigation://alpha/resale", "MITIGATION_RECORD"),
    ]
    if include_contract:
        documents.append(
            _document(
                "D-CONTRACT",
                "contract://alpha/termination-clause",
                "CONTRACT",
                signed=True,
            )
        )
    for document in documents:
        gateway.store_evidence_document(token, document)
    return event


def test_shadow_customer_save_leave_return_preserves_case_and_delivery_truth(tmp_path):
    database = tmp_path / "shadow.db"
    first = Storage(database)
    first.create_workspace("SHADOW", "Alpha Components Shadow")
    gateway = RecoveryRadarGateway(first)
    admin_token = gateway.bootstrap_workspace_admin("SHADOW", "owner")
    analyst_token = gateway.issue_key(admin_token, "analyst", "ANALYST")
    event = _seed_alpha(gateway, analyst_token)

    before = gateway.build_claim_package(analyst_token, event.event_id, "SUP-ALPHA")
    case = gateway.create_case(analyst_token, event.event_id, "SUP-ALPHA")
    digest_before_leave = first.economic_digest("SHADOW")
    assert REQUIRED_DELIVERY_SECTIONS.issubset(before)
    assert before["executive_summary"]["claimable_total"] == "800.00"
    assert before["draft_claim_package"]["status"] == "DRAFT_NOT_SUBMITTED"
    assert before["draft_claim_package"]["claimable_total"] == "800.00"
    assert case.claim_amount == Decimal("800.00")
    assert case.event_id == event.event_id
    assert case.analysis_fingerprint
    first.close()

    second = Storage(database)
    try:
        returned = RecoveryRadarGateway(second)
        authenticated = returned.auth.authenticate(analyst_token)
        assert authenticated.workspace_id == "SHADOW"
        recovered_case = returned.get_case(analyst_token, case.case_id)
        after = returned.build_claim_package(
            analyst_token, event.event_id, "SUP-ALPHA"
        )
        assert second.economic_digest("SHADOW") == digest_before_leave
        assert recovered_case == case
        assert after["executive_summary"]["net_exposure_total"] == before["executive_summary"]["net_exposure_total"]
        assert after["executive_summary"]["claimable_total"] == "800.00"
        assert after["recoverability"] == before["recoverability"]
        assert after["calculation_trace"] == before["calculation_trace"]
        assert after["audit_trail"]
        assert after["audit_event_count"] == len(after["audit_trail"])
        assert all(item["entity_id"] for item in after["audit_trail"])
    finally:
        second.close()


def test_shadow_customer_incomplete_evidence_stays_explicitly_non_claim_ready(tmp_path):
    store = Storage(tmp_path / "incomplete.db")
    try:
        store.create_workspace("SHADOW", "Incomplete Shadow")
        gateway = RecoveryRadarGateway(store)
        admin_token = gateway.bootstrap_workspace_admin("SHADOW", "owner")
        analyst_token = gateway.issue_key(admin_token, "analyst", "ANALYST")
        event = _seed_alpha(gateway, analyst_token, include_contract=False)
        package = gateway.build_claim_package(
            analyst_token, event.event_id, "SUP-ALPHA"
        )
        assert package["executive_summary"]["claimable_total"] == "0.00"
        assert package["review_status"] == "REQUIRES_HUMAN_REVIEW"
        assert package["uncertainty"]
        assert any(
            "UNREGISTERED_EVIDENCE:contract://alpha/termination-clause" in issue
            for issue in package["registered_evidence_issues"]
        )
        assert package["draft_claim_package"]["claimable_total"] == "0.00"
        assert package["draft_claim_package"]["lines"] == []
    finally:
        store.close()
