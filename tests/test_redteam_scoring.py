from recovery_radar.engine import analyze_claim
from recovery_radar.scoring import score_claim_lines
from recovery_radar.synthetic import redteam_industrial_fixture


def test_redteam_industrial_matches_independent_ground_truth_without_false_claims():
    event, exposures, entitlements, truth = redteam_industrial_fixture()
    analysis = analyze_claim(event, exposures, entitlements)
    score = score_claim_lines(analysis["claim_lines"], truth)
    assert score == {
        "status":"SCORED",
        "false_claims":0,
        "missed_claims":0,
        "overclaims":0,
        "underclaims":0,
        "state_mismatches":0,
        "truth_claimable_total":"670.00",
        "predicted_claimable_or_review_total":"670.00",
        "absolute_value_error":"0.00",
    }
    assert analysis["claimable_total"] == "250.00"
    assert analysis["requires_review_amount"] == "420.00"
    assert analysis["paid_total"] == "0.00"


def test_scorer_rejects_scope_mismatch_instead_of_grading_partial_dataset():
    event, exposures, entitlements, truth = redteam_industrial_fixture()
    analysis = analyze_claim(event, exposures, entitlements)
    reduced = dict(truth)
    reduced.pop("RT-9")
    result = score_claim_lines(analysis["claim_lines"], reduced)
    assert result["status"] == "INVALID_GROUND_TRUTH_SCOPE"
    assert result["unexpected_predictions"] == ["RT-9"]
