from decimal import Decimal

from recovery_radar.engine import analyze_claim
from recovery_radar.models import EntitlementBasis, ExposureLine
from recovery_radar.oracle import capped_claim, net_exposure
from recovery_radar.package import build_claim_package
from recovery_radar.synthetic import alpha_components_fixture, partial_recovery_fixture, zero_recovery_fixture


def test_alpha_clean_cancellation_matches_independent_oracle():
    event, exposures, entitlements, truth = alpha_components_fixture()
    result = analyze_claim(event, exposures, entitlements)
    assert net_exposure("100","10","200") == truth["net_exposure_total"] == "800.00"
    assert result["net_exposure_total"] == "800.00"
    assert result["claimable_total"] == truth["claimable_total"]
    assert result["paid_total"] == "0.00"
    assert result["claim_lines"][0]["state"] == "CLAIMABLE"


def test_large_exposure_can_have_zero_defensible_claim():
    event, exposures, entitlements, truth = zero_recovery_fixture()
    result = analyze_claim(event, exposures, entitlements)
    assert result["net_exposure_total"] == truth["net_exposure_total"]
    assert result["claimable_total"] == "0.00"
    assert result["claim_lines"][0]["reason"] == "ENTITLEMENT_NOT_SUPPORTED"


def test_partial_support_never_reports_full_exposure_as_claimable():
    event, exposures, entitlements, truth = partial_recovery_fixture()
    result = analyze_claim(event, exposures, entitlements)
    assert capped_claim("1000000","420000") == "420000.00"
    assert result["claimable_total"] == "0.00"
    assert result["requires_review_amount"] == truth["requires_review_amount"]
    assert result["claim_lines"][0]["state"] == "REQUIRES_REVIEW"


def test_partial_support_without_cap_fails_closed():
    event, exposures, _, _ = partial_recovery_fixture()
    basis = EntitlementBasis("E",event.event_id,"LOSS-P1","PARTIALLY_SUPPORTED","contract://x","doc://x")
    result = analyze_claim(event, exposures, [basis])
    assert result["claim_lines"][0]["state"] == "POTENTIAL_ENTITLEMENT"
    assert result["claim_lines"][0]["claimable_amount"] is None


def test_missing_contract_is_exposure_not_entitlement():
    event, exposures, _, _ = alpha_components_fixture()
    line = analyze_claim(event, exposures, [])["claim_lines"][0]
    assert line["state"] == "POTENTIAL_EXPOSURE"
    assert line["claimable_amount"] is None
    assert "MISSING_CONTRACTUAL_BASIS" in line["missing_evidence"]


def test_unknown_ownership_fails_closed():
    event, exposures, entitlements, _ = alpha_components_fixture()
    base = exposures[0]
    line = ExposureLine(base.exposure_id,base.event_id,base.economic_loss_id,base.category,base.quantity,base.unit_cost,base.currency,base.inventory_or_cost_ref,"UNKNOWN",base.mitigation_amount,base.mitigation_evidence_ref)
    result = analyze_claim(event,[line],entitlements)["claim_lines"][0]
    assert result["state"] == "UNKNOWN"
    assert "MISSING_OWNERSHIP_EVIDENCE" in result["missing_evidence"]


def test_customer_owned_inventory_is_not_supplier_claim():
    event, exposures, entitlements, _ = alpha_components_fixture()
    base = exposures[0]
    line = ExposureLine(base.exposure_id,base.event_id,base.economic_loss_id,base.category,base.quantity,base.unit_cost,base.currency,base.inventory_or_cost_ref,"CUSTOMER",base.mitigation_amount,base.mitigation_evidence_ref)
    result = analyze_claim(event,[line],entitlements)["claim_lines"][0]
    assert result["claimable_amount"] == "0.00"


def test_duplicate_economic_loss_is_never_double_counted_as_claimable():
    event, exposures, entitlements, _ = alpha_components_fixture()
    first = exposures[0]
    duplicate = ExposureLine("EXP-A2",event.event_id,first.economic_loss_id,"WIP",Decimal("50"),Decimal("20"),"EUR","inventory://alpha/WIP","SUPPLIER")
    result = analyze_claim(event,[first,duplicate],entitlements)
    assert result["claimable_total"] == "0.00"
    assert all(line["state"] == "UNKNOWN" for line in result["claim_lines"])


def test_conflicting_entitlement_records_fail_closed():
    event, exposures, entitlements, _ = alpha_components_fixture()
    second = EntitlementBasis("ENT-A2",event.event_id,"LOSS-A1","SUPPORTED","contract://other","doc://other")
    result = analyze_claim(event,exposures,[*entitlements,second])["claim_lines"][0]
    assert result["reason"] == "CONFLICTING_ENTITLEMENT_RECORDS"


def test_mitigation_cannot_exceed_gross_exposure():
    event, exposures, entitlements, _ = alpha_components_fixture()
    base = exposures[0]
    line = ExposureLine(base.exposure_id,base.event_id,base.economic_loss_id,base.category,base.quantity,base.unit_cost,base.currency,base.inventory_or_cost_ref,base.ownership,Decimal("2000"),"mitigation://x")
    result = analyze_claim(event,[line],entitlements)["claim_lines"][0]
    assert result["reason"] == "MITIGATION_EXCEEDS_GROSS_EXPOSURE"


def test_already_reimbursed_amount_reduces_claim_but_not_paid_total():
    event, exposures, entitlements, _ = alpha_components_fixture()
    base = exposures[0]
    line = ExposureLine(base.exposure_id,base.event_id,base.economic_loss_id,base.category,base.quantity,base.unit_cost,base.currency,base.inventory_or_cost_ref,base.ownership,base.mitigation_amount,base.mitigation_evidence_ref,Decimal("100"),"credit://alpha/CN1")
    result = analyze_claim(event,[line],entitlements)
    assert result["claimable_total"] == "700.00"
    assert result["paid_total"] == "0.00"


def test_reimbursed_amount_without_evidence_blocks_claimability():
    event, exposures, entitlements, _ = alpha_components_fixture()
    base = exposures[0]
    line = ExposureLine(base.exposure_id,base.event_id,base.economic_loss_id,base.category,base.quantity,base.unit_cost,base.currency,base.inventory_or_cost_ref,base.ownership,base.mitigation_amount,base.mitigation_evidence_ref,Decimal("100"),None)
    result = analyze_claim(event,[line],entitlements)["claim_lines"][0]
    assert result["state"] == "POTENTIAL_ENTITLEMENT"
    assert "MISSING_REIMBURSEMENT_EVIDENCE" in result["missing_evidence"]


def test_event_reference_mismatch_fails_closed():
    event, exposures, entitlements, _ = alpha_components_fixture()
    base = exposures[0]
    line = ExposureLine(base.exposure_id,"OTHER-EVENT",base.economic_loss_id,base.category,base.quantity,base.unit_cost,base.currency,base.inventory_or_cost_ref,base.ownership)
    result = analyze_claim(event,[line],entitlements)["claim_lines"][0]
    assert result["reason"] == "EVENT_REFERENCE_MISMATCH"


def test_claim_package_exposes_missing_evidence_and_legal_boundary():
    event, exposures, _, _ = alpha_components_fixture()
    package = build_claim_package(analyze_claim(event,exposures,[]))
    assert "MISSING_CONTRACTUAL_BASIS" in package["missing_evidence"]
    assert package["review_status"] == "REQUIRES_HUMAN_REVIEW"
    assert package["legal_boundary"] == "ECONOMIC_AND_EVIDENCE_ASSISTANCE_NOT_LEGAL_DETERMINATION"


def test_paid_total_is_never_inferred_from_claim_value():
    event, exposures, entitlements, _ = alpha_components_fixture()
    result = analyze_claim(event,exposures,entitlements)
    assert result["claimable_total"] == "800.00"
    assert result["paid_total"] == "0.00"
