from recovery_radar.claimability import apply_registered_evidence_gate
from recovery_radar.engine import analyze_claim
from recovery_radar.missing_evidence import build_missing_evidence_actions
from recovery_radar.package import build_claim_package
from recovery_radar.synthetic import alpha_components_fixture


def test_missing_contract_action_identifies_line_proof_holder_and_value_ceiling():
    event, exposures, _, _ = alpha_components_fixture()
    analysis = analyze_claim(event, exposures, [])
    actions = build_missing_evidence_actions(analysis)
    contract = next(
        item for item in actions if item["evidence_code"] == "MISSING_CONTRACTUAL_BASIS"
    )
    assert contract["exposure_id"] == "EXP-A1"
    assert contract["economic_loss_id"] == "LOSS-A1"
    assert contract["what_it_would_prove"] == "CONTRACTUAL_OR_COMMERCIAL_BASIS_FOR_RECOVERABILITY"
    assert contract["likely_holder_hint"] == "SUPPLIER_COMMERCIAL_LEGAL_OR_CUSTOMER_PROCUREMENT"
    assert contract["can_claim_proceed_without_it"] is False
    assert contract["blocked_or_upper_bound_value"] == "800.00"
    assert contract["value_basis"] == "NET_EXPOSURE_UPPER_BOUND_NOT_RECOVERABLE_AMOUNT"
    assert contract["currency"] == "EUR"
    assert contract["obtainability_likelihood"] == "UNKNOWN"
    assert contract["priority_score_value_x_likelihood"] is None


def test_unregistered_required_source_reports_modeled_amount_blocked_not_fake_probability():
    event, exposures, entitlements, _ = alpha_components_fixture()
    raw = analyze_claim(event, exposures, entitlements)
    gated = apply_registered_evidence_gate(
        raw, [], workspace_id="A", supplier_id="SUP-A"
    )
    actions = build_missing_evidence_actions(gated)
    contract = next(
        item
        for item in actions
        if item["missing_evidence"]
        == "UNREGISTERED_EVIDENCE:contract://alpha/termination-clause"
    )
    assert contract["blocked_or_upper_bound_value"] == "800.00"
    assert contract["value_basis"] == "MODELED_AMOUNT_BLOCKED_BY_EVIDENCE_GATE"
    assert contract["obtainability_likelihood"] == "UNKNOWN"
    assert contract["priority_state"] == "AWAITING_OBTAINABILITY_ESTIMATE"


def test_claim_package_surfaces_action_plan_for_missing_evidence():
    event, exposures, _, _ = alpha_components_fixture()
    package = build_claim_package(analyze_claim(event, exposures, []))
    assert package["missing_evidence_actions"]
    assert all(item["exposure_id"] for item in package["missing_evidence_actions"])
    assert package["review_status"] == "REQUIRES_HUMAN_REVIEW"
