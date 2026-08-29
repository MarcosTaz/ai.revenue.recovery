from datetime import date
from decimal import Decimal

from recovery_radar.claimability import apply_registered_evidence_gate
from recovery_radar.engine import analyze_claim
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.models import EntitlementBasis, ExposureLine, RecoveryEvent
from recovery_radar.scoring import score_claim_lines


def event(evidence_ref="notice://1"):
    return RecoveryEvent(
        "EV-PF", "OEM-PF", "PRG-PF", "PART-PF", "PROGRAM_CANCELLED",
        date(2026, 7, 1), Decimal("1000"), Decimal("0"),
        "event://PF", evidence_ref,
    )


def line(exposure_id, loss_id, category, quantity, unit_cost, **kwargs):
    return ExposureLine(
        exposure_id, "EV-PF", loss_id, category, Decimal(quantity), Decimal(unit_cost),
        kwargs.pop("currency", "EUR"), kwargs.pop("inventory_or_cost_ref", f"cost://{exposure_id}"),
        kwargs.pop("ownership", "SUPPLIER"), **kwargs,
    )


def basis(entitlement_id, loss_id, state="SUPPORTED", **kwargs):
    return EntitlementBasis(
        entitlement_id, "EV-PF", loss_id, state,
        kwargs.pop("contractual_basis_ref", f"contract://{entitlement_id}"),
        kwargs.pop("supporting_document_ref", f"support://{entitlement_id}"),
        **kwargs,
    )


def test_wip_partially_recoverable_is_capped_and_requires_review():
    result = analyze_claim(
        event(),
        [line("WIP-1", "L-WIP", "WIP", "10", "100", mitigation_amount=Decimal("200"), mitigation_evidence_ref="reuse://WIP-1")],
        [basis("E-WIP", "L-WIP", "PARTIALLY_SUPPORTED", recoverable_cap=Decimal("500"), legal_review_required=True)],
    )
    truth = {"WIP-1": {"expected_state": "REQUIRES_REVIEW", "claimable_amount": "500.00"}}
    score = score_claim_lines(result["claim_lines"], truth)
    assert score["absolute_value_error"] == "0.00"
    assert score["state_mismatches"] == 0
    assert result["requires_review_amount"] == "500.00"


def test_finished_goods_already_fully_compensated_returns_zero_recovery():
    result = analyze_claim(
        event(),
        [line("FG-1", "L-FG", "FINISHED_GOODS", "10", "100", already_reimbursed_amount=Decimal("1000"), reimbursement_evidence_ref="credit://FG-1")],
        [basis("E-FG", "L-FG")],
    )
    claim = result["claim_lines"][0]
    assert result["claimable_total"] == "0.00"
    assert claim["state"] == "POTENTIAL_EXPOSURE"
    assert claim["reason"] == "NO_NET_EXPOSURE_AFTER_OFFSETS"


def test_nre_already_amortized_returns_zero_recovery():
    result = analyze_claim(
        event(),
        [line("NRE-1", "L-NRE", "NRE", "1", "1000", mitigation_amount=Decimal("1000"), mitigation_evidence_ref="amortization://NRE-1")],
        [basis("E-NRE", "L-NRE")],
    )
    assert result["net_exposure_total"] == "0.00"
    assert result["claimable_total"] == "0.00"
    assert result["claim_lines"][0]["reason"] == "NO_NET_EXPOSURE_AFTER_OFFSETS"


def test_avoidable_supplier_commitment_fully_cancelled_is_not_claimed():
    result = analyze_claim(
        event(),
        [line("SC-A", "L-SCA", "SUPPLIER_COMMITMENTS", "1", "600", mitigation_amount=Decimal("600"), mitigation_evidence_ref="supplier-cancel://SC-A")],
        [basis("E-SCA", "L-SCA")],
    )
    assert result["claimable_total"] == "0.00"
    assert result["claim_lines"][0]["net_exposure"] == "0.00"


def test_unavoidable_supplier_commitment_can_remain_claimable_when_supported():
    result = analyze_claim(
        event(),
        [line("SC-U", "L-SCU", "SUPPLIER_COMMITMENTS", "1", "600")],
        [basis("E-SCU", "L-SCU")],
    )
    assert result["claimable_total"] == "600.00"
    assert result["claim_lines"][0]["state"] == "CLAIMABLE"


def test_prior_credit_reduces_claim_and_never_becomes_paid_total():
    result = analyze_claim(
        event(),
        [line("CR-1", "L-CR", "RAW_MATERIAL", "10", "100", already_reimbursed_amount=Decimal("250"), reimbursement_evidence_ref="credit://CR-1")],
        [basis("E-CR", "L-CR")],
    )
    assert result["claimable_total"] == "750.00"
    assert result["paid_total"] == "0.00"


def test_loss_without_entitlement_is_not_claimable():
    result = analyze_claim(event(), [line("NO-E", "L-NO-E", "RAW_MATERIAL", "10", "100")], [])
    claim = result["claim_lines"][0]
    assert claim["state"] == "POTENTIAL_EXPOSURE"
    assert claim["claimable_amount"] is None


def test_entitlement_with_missing_cost_evidence_is_not_claimable():
    result = analyze_claim(
        event(),
        [line("MISS-COST", "L-MC", "RAW_MATERIAL", "10", "100", inventory_or_cost_ref="")],
        [basis("E-MC", "L-MC")],
    )
    claim = result["claim_lines"][0]
    assert claim["state"] == "POTENTIAL_ENTITLEMENT"
    assert "MISSING_INVENTORY_OR_COST_RECORD" in claim["missing_evidence"]


def test_expired_right_encoded_as_reviewed_not_supported_entitlement_returns_zero():
    result = analyze_claim(
        event(),
        [line("EXP-RIGHT", "L-EXP", "TOOLING", "1", "2000")],
        [basis("E-EXPIRED", "L-EXP", "NOT_SUPPORTED", contractual_basis_ref="contract://expired-right", supporting_document_ref="review://expiry-confirmed")],
    )
    claim = result["claim_lines"][0]
    assert claim["state"] == "POTENTIAL_EXPOSURE"
    assert claim["reason"] == "ENTITLEMENT_NOT_SUPPORTED"
    assert claim["claimable_amount"] == "0.00"


def test_conflicting_contract_versions_fail_closed():
    result = analyze_claim(
        event(),
        [line("CONFLICT", "L-CONFLICT", "RAW_MATERIAL", "10", "100")],
        [
            basis("E-V1", "L-CONFLICT", "SUPPORTED", contractual_basis_ref="contract://v1"),
            basis("E-V2", "L-CONFLICT", "NOT_SUPPORTED", contractual_basis_ref="contract://v2"),
        ],
    )
    assert result["claim_lines"][0]["state"] == "UNKNOWN"
    assert result["claim_lines"][0]["reason"] == "CONFLICTING_ENTITLEMENT_RECORDS"


def test_missing_amendment_support_document_blocks_claimability():
    result = analyze_claim(
        event(),
        [line("AMEND", "L-AMEND", "TOOLING", "1", "2000")],
        [basis("E-AMEND", "L-AMEND", supporting_document_ref=None)],
    )
    claim = result["claim_lines"][0]
    assert claim["state"] == "POTENTIAL_ENTITLEMENT"
    assert "MISSING_SUPPORTING_DOCUMENT" in claim["missing_evidence"]


def test_missing_cancellation_evidence_fails_registered_evidence_gate():
    raw = analyze_claim(
        event(evidence_ref=""),
        [line("NO-NOTICE", "L-NN", "RAW_MATERIAL", "10", "100")],
        [basis("E-NN", "L-NN")],
    )
    documents = [
        EvidenceDocument.from_bytes(document_id="D-I",workspace_id="A",supplier_id="SUP",customer_id="OEM-PF",program_id="PRG-PF",evidence_type="INVENTORY_RECORD",source_ref="cost://NO-NOTICE",version_id="v1",document_date=date(2026,7,1),content=b"inventory"),
        EvidenceDocument.from_bytes(document_id="D-C",workspace_id="A",supplier_id="SUP",customer_id="OEM-PF",program_id="PRG-PF",evidence_type="CONTRACT",source_ref="contract://E-NN",version_id="v1",document_date=date(2026,1,1),content=b"contract",signed=True),
        EvidenceDocument.from_bytes(document_id="D-S",workspace_id="A",supplier_id="SUP",customer_id="OEM-PF",program_id="PRG-PF",evidence_type="PURCHASE_ORDER",source_ref="support://E-NN",version_id="v1",document_date=date(2026,1,1),content=b"support"),
    ]
    gated = apply_registered_evidence_gate(raw, documents, workspace_id="A", supplier_id="SUP")
    assert gated["claimable_total"] == "0.00"
    assert "MISSING_REQUIRED_EVIDENCE_REFERENCE" in gated["claim_lines"][0]["registered_evidence_issues"]
