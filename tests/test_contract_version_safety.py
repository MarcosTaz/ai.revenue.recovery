from datetime import date

from recovery_radar.claimability import apply_registered_evidence_gate
from recovery_radar.engine import analyze_claim
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.synthetic import alpha_components_fixture


def _doc(document_id, source_ref, evidence_type, *, version_id="v1", document_date=date(2026, 1, 1), signed=None):
    return EvidenceDocument.from_bytes(
        document_id=document_id,
        workspace_id="A",
        supplier_id="SUP-A",
        customer_id="OEM-A",
        program_id="PRG-A",
        evidence_type=evidence_type,
        source_ref=source_ref,
        version_id=version_id,
        document_date=document_date,
        content=f"{document_id}:{source_ref}:{version_id}:{document_date.isoformat()}".encode(),
        signed=signed,
    )


def _base_documents(contract):
    return [
        _doc("D-N", "document://alpha/customer-notice", "CUSTOMER_NOTICE"),
        _doc("D-I", "inventory://alpha/A1", "INVENTORY_RECORD"),
        contract,
        _doc("D-P", "po://alpha/PO-1", "PURCHASE_ORDER"),
        _doc("D-M", "mitigation://alpha/resale", "MITIGATION_RECORD"),
    ]


def test_post_event_contract_cannot_support_money_without_independent_verification():
    event, exposures, entitlements, _ = alpha_components_fixture()
    later_contract = _doc(
        "D-C-LATER",
        "contract://alpha/termination-clause",
        "CONTRACT",
        version_id="v2",
        document_date=date(2026, 8, 1),
        signed=True,
    )
    docs = _base_documents(later_contract)
    verified_ids = {doc.document_id for doc in docs if doc.document_id != "D-C-LATER"}
    gated = apply_registered_evidence_gate(
        analyze_claim(event, exposures, entitlements),
        docs,
        workspace_id="A",
        supplier_id="SUP-A",
        verified_document_ids=verified_ids,
        require_verification=True,
    )
    line = gated["claim_lines"][0]
    assert gated["claimable_total"] == "0.00"
    assert line["state"] == "POTENTIAL_ENTITLEMENT"
    assert "EVIDENCE_NOT_VERIFIED:contract://alpha/termination-clause" in line["registered_evidence_issues"]


def test_multiple_contract_versions_for_same_source_fail_closed_even_if_both_verified():
    event, exposures, entitlements, _ = alpha_components_fixture()
    old_contract = _doc(
        "D-C-V1",
        "contract://alpha/termination-clause",
        "CONTRACT",
        version_id="v1",
        document_date=date(2026, 1, 1),
        signed=True,
    )
    later_contract = _doc(
        "D-C-V2",
        "contract://alpha/termination-clause",
        "CONTRACT",
        version_id="v2",
        document_date=date(2026, 8, 1),
        signed=True,
    )
    docs = _base_documents(old_contract) + [later_contract]
    gated = apply_registered_evidence_gate(
        analyze_claim(event, exposures, entitlements),
        docs,
        workspace_id="A",
        supplier_id="SUP-A",
        verified_document_ids={doc.document_id for doc in docs},
        require_verification=True,
    )
    line = gated["claim_lines"][0]
    assert gated["claimable_total"] == "0.00"
    assert line["state"] == "POTENTIAL_ENTITLEMENT"
    assert "AMBIGUOUS_REGISTERED_SOURCE:contract://alpha/termination-clause" in line["registered_evidence_issues"]
