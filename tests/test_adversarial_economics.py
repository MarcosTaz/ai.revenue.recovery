from dataclasses import replace
from decimal import Decimal

from recovery_radar.case_factory import case_from_gated_analysis
from recovery_radar.engine import analyze_claim
from recovery_radar.models import EntitlementBasis, ExposureLine
from recovery_radar.package import build_claim_package
from recovery_radar.synthetic import alpha_components_fixture


def test_mixed_currency_never_emits_false_scalar_total():
    event, exposures, entitlements, _ = alpha_components_fixture()
    usd = ExposureLine(
        "EXP-USD",
        event.event_id,
        "LOSS-USD",
        "WIP",
        Decimal("10"),
        Decimal("20"),
        "USD",
        "inventory://alpha/usd",
        "SUPPLIER",
    )
    usd_basis = EntitlementBasis(
        "ENT-USD",
        event.event_id,
        "LOSS-USD",
        "SUPPORTED",
        "contract://alpha/usd",
        "po://alpha/usd",
    )
    result = analyze_claim(event, [*exposures, usd], [*entitlements, usd_basis])
    assert result["mixed_currency"] is True
    assert result["net_exposure_total"] is None
    assert result["claimable_total"] is None
    assert result["requires_review_amount"] is None
    assert result["totals_by_currency"]["EUR"]["claimable_total"] == "800.00"
    assert result["totals_by_currency"]["USD"]["claimable_total"] == "200.00"

    package = build_claim_package(result)
    assert package["review_status"] == "MULTI_CURRENCY_SPLIT_REQUIRED"
    assert package["draft_claim_package"]["status"] == "MULTI_CURRENCY_SPLIT_REQUIRED"
    assert package["executive_summary"]["claimable_total"] is None


def test_multi_currency_case_must_be_split_even_when_lines_are_gate_passed():
    event, exposures, entitlements, _ = alpha_components_fixture()
    usd = ExposureLine(
        "EXP-USD",
        event.event_id,
        "LOSS-USD",
        "WIP",
        Decimal("10"),
        Decimal("20"),
        "USD",
        "inventory://alpha/usd",
        "SUPPLIER",
    )
    usd_basis = EntitlementBasis(
        "ENT-USD",
        event.event_id,
        "LOSS-USD",
        "SUPPORTED",
        "contract://alpha/usd",
        "po://alpha/usd",
    )
    gated = analyze_claim(event, [*exposures, usd], [*entitlements, usd_basis])
    gated["registered_evidence_gate"] = "APPLIED"
    for line in gated["claim_lines"]:
        line["registered_evidence_gate"] = "PASSED"
    try:
        case_from_gated_analysis("A", gated)
    except ValueError as exc:
        assert str(exc) == "MULTI_CURRENCY_CLAIM_CASE_REQUIRES_SPLIT"
    else:
        raise AssertionError("mixed-currency claim case was incorrectly created")


def test_non_finite_quantity_fails_closed_instead_of_crashing():
    event, exposures, entitlements, _ = alpha_components_fixture()
    corrupt = replace(exposures[0], quantity=Decimal("NaN"))
    result = analyze_claim(event, [corrupt], entitlements)
    line = result["claim_lines"][0]
    assert line["state"] == "UNKNOWN"
    assert line["reason"] == "NON_FINITE_ECONOMIC_INPUT"
    assert result["claimable_total"] == "0.00"


def test_non_finite_recoverable_cap_fails_closed():
    event, exposures, entitlements, _ = alpha_components_fixture()
    corrupt_basis = replace(entitlements[0], recoverable_cap=Decimal("Infinity"))
    line = analyze_claim(event, exposures, [corrupt_basis])["claim_lines"][0]
    assert line["state"] == "UNKNOWN"
    assert line["reason"] == "NON_FINITE_RECOVERABLE_CAP"


def test_extreme_finite_value_outside_supported_numeric_envelope_fails_closed():
    event, exposures, entitlements, _ = alpha_components_fixture()
    extreme = replace(exposures[0], quantity=Decimal("1E+101"))
    line = analyze_claim(event, [extreme], entitlements)["claim_lines"][0]
    assert line["state"] == "UNKNOWN"
    assert line["reason"] == "ECONOMIC_INPUT_OUT_OF_SUPPORTED_RANGE"


def test_invalid_event_economics_cannot_produce_claimable_amount():
    event, exposures, entitlements, _ = alpha_components_fixture()
    corrupt_event = replace(event, expected_volume=Decimal("Infinity"))
    result = analyze_claim(corrupt_event, exposures, entitlements)
    assert result["event"]["impacted_volume"] is None
    assert result["claimable_total"] == "0.00"
    assert result["claim_lines"][0]["state"] == "UNKNOWN"
    assert result["claim_lines"][0]["reason"] == "INVALID_EVENT_ECONOMIC_INPUT"


def test_exact_duplicate_economic_representation_with_different_ids_fails_closed():
    event, exposures, entitlements, _ = alpha_components_fixture()
    original = exposures[0]
    duplicate = replace(
        original,
        exposure_id="EXP-ALIAS",
        economic_loss_id="LOSS-ALIAS",
    )
    duplicate_basis = EntitlementBasis(
        "ENT-ALIAS",
        event.event_id,
        "LOSS-ALIAS",
        "SUPPORTED",
        "contract://alpha/termination-clause",
        "po://alpha/PO-1",
    )
    result = analyze_claim(event, [original, duplicate], [*entitlements, duplicate_basis])
    assert result["claimable_total"] == "0.00"
    assert all(line["state"] == "UNKNOWN" for line in result["claim_lines"])
    assert all(
        line["reason"] == "DUPLICATE_ECONOMIC_REPRESENTATION_REQUIRES_REVIEW"
        for line in result["claim_lines"]
    )
