from __future__ import annotations

from decimal import Decimal

POSITIVE_STATES = {"CLAIMABLE", "REQUIRES_REVIEW"}


def score_claim_lines(results: list[dict], truth: dict[str, dict]) -> dict:
    """Independent scorer. It does not import or execute the claim engine."""
    predicted = {r["lineage"]["exposure_id"]: r for r in results}
    if set(predicted) != set(truth):
        return {
            "status": "INVALID_GROUND_TRUTH_SCOPE",
            "missing_predictions": sorted(set(truth) - set(predicted)),
            "unexpected_predictions": sorted(set(predicted) - set(truth)),
        }

    false_claims = missed_claims = overclaims = underclaims = 0
    state_mismatches = 0
    absolute_value_error = Decimal("0")
    truth_total = Decimal("0")
    predicted_total = Decimal("0")

    for exposure_id, reference in truth.items():
        result = predicted[exposure_id]
        expected_amount = Decimal(reference["claimable_amount"])
        predicted_amount = Decimal(result.get("claimable_amount") or "0")
        expected_positive = expected_amount > 0
        predicted_positive = result["state"] in POSITIVE_STATES and predicted_amount > 0
        truth_total += expected_amount
        predicted_total += predicted_amount
        absolute_value_error += abs(predicted_amount - expected_amount)
        if predicted_positive and not expected_positive:
            false_claims += 1
        if expected_positive and not predicted_positive:
            missed_claims += 1
        if predicted_amount > expected_amount:
            overclaims += 1
        if predicted_amount < expected_amount:
            underclaims += 1
        if reference.get("expected_state") is not None and result["state"] != reference["expected_state"]:
            state_mismatches += 1

    return {
        "status": "SCORED",
        "false_claims": false_claims,
        "missed_claims": missed_claims,
        "overclaims": overclaims,
        "underclaims": underclaims,
        "state_mismatches": state_mismatches,
        "truth_claimable_total": str(truth_total.quantize(Decimal("0.01"))),
        "predicted_claimable_or_review_total": str(predicted_total.quantize(Decimal("0.01"))),
        "absolute_value_error": str(absolute_value_error.quantize(Decimal("0.01"))),
    }
