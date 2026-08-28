from datetime import date
from decimal import Decimal

import pytest

from recovery_radar.auth import Principal
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.service import TenantService
from recovery_radar.storage import Storage
from recovery_radar.synthetic import alpha_components_fixture, partial_recovery_fixture
from recovery_radar.workflow import ClaimCase


def principal():
    return Principal("A", "analyst", "ANALYST")


def reviewer():
    return Principal("A", "reviewer", "REVIEWER")


def document(document_id, source_ref, evidence_type, *, customer, program, supplier="SUP-A", signed=None):
    return EvidenceDocument.from_bytes(
        document_id=document_id,
        workspace_id="A",
        supplier_id=supplier,
        customer_id=customer,
        program_id=program,
        evidence_type=evidence_type,
        source_ref=source_ref,
        version_id="v1",
        document_date=date(2026, 1, 1),
        content=f"{document_id}:{source_ref}".encode(),
        signed=signed,
    )


def seed_alpha(service, *, with_documents=True, verify_documents=True):
    event, exposures, entitlements, _ = alpha_components_fixture()
    p = principal()
    service.store_recovery_event(p, event)
    for line in exposures:
        service.store_exposure_line(p, line)
    for basis in entitlements:
        service.store_entitlement_basis(p, basis)
    if with_documents:
        for doc in (
            document("D-N", "document://alpha/customer-notice", "CUSTOMER_NOTICE", customer="OEM-A", program="PRG-A"),
            document("D-I", "inventory://alpha/A1", "INVENTORY_RECORD", customer="OEM-A", program="PRG-A"),
            document("D-C", "contract://alpha/termination-clause", "CONTRACT", customer="OEM-A", program="PRG-A", signed=True),
            document("D-P", "po://alpha/PO-1", "PURCHASE_ORDER", customer="OEM-A", program="PRG-A"),
            document("D-M", "mitigation://alpha/resale", "MITIGATION_RECORD", customer="OEM-A", program="PRG-A"),
        ):
            service.store_evidence_document(p, doc)
            if verify_documents:
                service.review_evidence_document(reviewer(), doc.document_id, "VERIFIED", "synthetic fixture reviewed")
    return event


def test_case_amount_id_currency_and_provenance_are_derived_not_caller_supplied(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        seed_alpha(service)
        case = service.create_case(principal(), "EV-ALPHA-1", "SUP-A")
        assert case.claim_amount == Decimal("800.00")
        assert case.currency == "EUR"
        assert case.event_id == "EV-ALPHA-1"
        assert case.selected_exposure_ids == ("EXP-A1",)
        assert case.analysis_fingerprint
        assert case.case_id.startswith("CASE-")
    finally:
        store.close()


def test_public_case_creation_interface_rejects_arbitrary_claim_amount_keyword(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        seed_alpha(service)
        with pytest.raises(TypeError):
            service.create_case(principal(), "EV-ALPHA-1", "SUP-A", claim_amount=Decimal("999999"))
    finally:
        store.close()


def test_missing_registered_evidence_cannot_be_promoted_into_claim_case(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        seed_alpha(service, with_documents=False)
        with pytest.raises(ValueError, match="NO_CLAIMABLE_REGISTERED_EVIDENCE_LINES"):
            service.create_case(principal(), "EV-ALPHA-1", "SUP-A")
    finally:
        store.close()


def test_registered_but_unverified_evidence_cannot_be_promoted_into_claim_case(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        seed_alpha(service, verify_documents=False)
        analysis = service.analyze_event(principal(), "EV-ALPHA-1", "SUP-A")
        assert analysis["claimable_total"] == "0.00"
        assert any(
            issue.startswith("EVIDENCE_NOT_VERIFIED:")
            for issue in analysis["claim_lines"][0]["registered_evidence_issues"]
        )
        with pytest.raises(ValueError, match="NO_CLAIMABLE_REGISTERED_EVIDENCE_LINES"):
            service.create_case(principal(), "EV-ALPHA-1", "SUP-A")
    finally:
        store.close()


def test_wrong_supplier_scope_cannot_be_promoted_into_claim_case(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        seed_alpha(service)
        with pytest.raises(ValueError, match="NO_CLAIMABLE_REGISTERED_EVIDENCE_LINES"):
            service.create_case(principal(), "EV-ALPHA-1", "WRONG-SUPPLIER")
    finally:
        store.close()


def test_selected_unknown_exposure_cannot_inflate_or_fabricate_claim(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        seed_alpha(service)
        with pytest.raises(ValueError, match="SELECTED_LINE_NOT_CLAIMABLE:EXP-FAKE"):
            service.create_case(
                principal(),
                "EV-ALPHA-1",
                "SUP-A",
                selected_exposure_ids=["EXP-A1", "EXP-FAKE"],
            )
    finally:
        store.close()


def test_complete_evidence_does_not_auto_promote_legal_review_line_to_claim(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        p = principal()
        event, exposures, entitlements, _ = partial_recovery_fixture()
        service.store_recovery_event(p, event)
        for line in exposures:
            service.store_exposure_line(p, line)
        for basis in entitlements:
            service.store_entitlement_basis(p, basis)
        for doc in (
            document("P-N", "document://partial/release", "CUSTOMER_NOTICE", customer="OEM-P", program="PRG-P", supplier="SUP-P"),
            document("P-I", "asset://partial/tool-1", "COST_RECORD", customer="OEM-P", program="PRG-P", supplier="SUP-P"),
            document("P-C", "agreement://partial/tooling", "CONTRACT", customer="OEM-P", program="PRG-P", supplier="SUP-P", signed=True),
            document("P-A", "approval://partial/cap", "TOOLING_APPROVAL", customer="OEM-P", program="PRG-P", supplier="SUP-P", signed=True),
        ):
            service.store_evidence_document(p, doc)
            service.review_evidence_document(reviewer(), doc.document_id, "VERIFIED", "synthetic fixture reviewed")
        analysis = service.analyze_event(p, event.event_id, "SUP-P")
        assert analysis["requires_review_amount"] == "420000.00"
        with pytest.raises(ValueError, match="NO_CLAIMABLE_REGISTERED_EVIDENCE_LINES"):
            service.create_case(p, event.event_id, "SUP-P")
    finally:
        store.close()


def test_low_level_storage_rejects_fabricated_case_without_source_provenance(tmp_path):
    store = Storage(tmp_path / "rr.db")
    try:
        store.create_workspace("A", "Supplier A")
        forged = ClaimCase("CASE-FAKE", "A", Decimal("999999"), "EUR")
        with pytest.raises(ValueError, match="CLAIM_CASE_PROVENANCE_REQUIRED"):
            store.put_claim_case("A", "attacker", forged)
    finally:
        store.close()
