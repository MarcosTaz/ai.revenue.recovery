from datetime import date

from recovery_radar.claimability import apply_registered_evidence_gate
from recovery_radar.engine import analyze_claim
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.package import build_claim_package
from recovery_radar.synthetic import alpha_components_fixture, partial_recovery_fixture


def evidence(source_ref, evidence_type, *, document_id, customer, program, signed=None, workspace="A", supplier="SUP-ALPHA"):
    return EvidenceDocument.from_bytes(
        document_id=document_id,
        workspace_id=workspace,
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


def alpha_documents():
    return [
        evidence("document://alpha/customer-notice", "CUSTOMER_NOTICE", document_id="D-NOTICE", customer="OEM-A", program="PRG-A"),
        evidence("inventory://alpha/A1", "INVENTORY_RECORD", document_id="D-INV", customer="OEM-A", program="PRG-A"),
        evidence("contract://alpha/termination-clause", "CONTRACT", document_id="D-CONTRACT", customer="OEM-A", program="PRG-A", signed=True),
        evidence("po://alpha/PO-1", "PURCHASE_ORDER", document_id="D-PO", customer="OEM-A", program="PRG-A"),
        evidence("mitigation://alpha/resale", "MITIGATION_RECORD", document_id="D-MIT", customer="OEM-A", program="PRG-A"),
    ]


def test_raw_claimable_analysis_is_not_package_ready_before_registry_gate():
    event, exposures, entitlements, _ = alpha_components_fixture()
    raw = analyze_claim(event, exposures, entitlements)
    assert raw["claimable_total"] == "800.00"
    package = build_claim_package(raw)
    assert package["review_status"] == "REGISTERED_EVIDENCE_GATE_REQUIRED"


def test_complete_registered_evidence_preserves_claimability_and_package_readiness():
    event, exposures, entitlements, _ = alpha_components_fixture()
    gated = apply_registered_evidence_gate(
        analyze_claim(event, exposures, entitlements),
        alpha_documents(),
        workspace_id="A",
        supplier_id="SUP-ALPHA",
    )
    assert gated["registered_evidence_gate"] == "APPLIED"
    assert gated["claimable_total"] == "800.00"
    assert gated["claim_lines"][0]["registered_evidence_gate"] == "PASSED"
    assert build_claim_package(gated)["review_status"] == "ECONOMIC_PACKAGE_READY_FOR_REVIEW"


def test_missing_registered_contract_downgrades_claimability():
    event, exposures, entitlements, _ = alpha_components_fixture()
    docs = [doc for doc in alpha_documents() if doc.source_ref != "contract://alpha/termination-clause"]
    gated = apply_registered_evidence_gate(
        analyze_claim(event, exposures, entitlements), docs, workspace_id="A", supplier_id="SUP-ALPHA"
    )
    line = gated["claim_lines"][0]
    assert line["state"] == "POTENTIAL_ENTITLEMENT"
    assert line["pre_gate_state"] == "CLAIMABLE"
    assert gated["claimable_total"] == "0.00"
    assert "UNREGISTERED_EVIDENCE:contract://alpha/termination-clause" in line["registered_evidence_issues"]


def test_wrong_program_registered_document_downgrades_claimability():
    event, exposures, entitlements, _ = alpha_components_fixture()
    docs = alpha_documents()
    docs = [
        evidence(
            doc.source_ref,
            doc.evidence_type,
            document_id=doc.document_id,
            customer=doc.customer_id,
            program="WRONG" if doc.document_id == "D-PO" else doc.program_id,
            signed=doc.signed,
        )
        for doc in docs
    ]
    gated = apply_registered_evidence_gate(
        analyze_claim(event, exposures, entitlements), docs, workspace_id="A", supplier_id="SUP-ALPHA"
    )
    assert gated["claim_lines"][0]["state"] == "POTENTIAL_ENTITLEMENT"
    assert any("WRONG_PROGRAM" in issue for issue in gated["claim_lines"][0]["registered_evidence_issues"])


def test_registered_evidence_does_not_bypass_legal_review_requirement():
    event, exposures, entitlements, _ = partial_recovery_fixture()
    docs = [
        evidence("document://partial/release", "CUSTOMER_NOTICE", document_id="P-NOTICE", customer="OEM-P", program="PRG-P", supplier="SUP-P"),
        evidence("asset://partial/tool-1", "COST_RECORD", document_id="P-ASSET", customer="OEM-P", program="PRG-P", supplier="SUP-P"),
        evidence("agreement://partial/tooling", "CONTRACT", document_id="P-CONTRACT", customer="OEM-P", program="PRG-P", supplier="SUP-P", signed=True),
        evidence("approval://partial/cap", "TOOLING_APPROVAL", document_id="P-APPROVAL", customer="OEM-P", program="PRG-P", supplier="SUP-P", signed=True),
    ]
    gated = apply_registered_evidence_gate(
        analyze_claim(event, exposures, entitlements), docs, workspace_id="A", supplier_id="SUP-P"
    )
    assert gated["claimable_total"] == "0.00"
    assert gated["requires_review_amount"] == "420000.00"
    assert gated["claim_lines"][0]["state"] == "REQUIRES_REVIEW"
    assert gated["claim_lines"][0]["registered_evidence_gate"] == "PASSED"
