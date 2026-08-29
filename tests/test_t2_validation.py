from decimal import Decimal

import pytest

from recovery_radar.engine import analyze_claim
from recovery_radar.synthetic import alpha_components_fixture
from recovery_radar.t2_validation import (
    GroundTruthLine,
    PilotOperationalMetrics,
    score_historical_case,
)


def _alpha_analysis():
    event, exposures, entitlements, _ = alpha_components_fixture()
    return analyze_claim(event, exposures, entitlements)


def test_exact_ground_truth_scores_zero_fp_fn_and_zero_value_error():
    analysis = _alpha_analysis()
    result = score_historical_case(
        analysis,
        [GroundTruthLine("LOSS-A1", "CLAIMABLE", "EUR", Decimal("800.00"))],
        ground_truth_complete=True,
        operational_metrics=PilotOperationalMetrics(
            analyst_preparation_minutes=Decimal("30"),
            reviewer_minutes=Decimal("12"),
            total_time_to_package_minutes=Decimal("50"),
            reviewer_evidence_corrections=1,
            reviewer_entitlement_corrections=0,
            missing_evidence_actions_useful=2,
            missing_evidence_actions_not_useful=0,
            repeat_use_signal="YES",
        ),
    )
    assert result["false_positive_count"] == 0
    assert result["false_negative_count"] == 0
    assert result["state_mismatches"] == []
    assert result["amount_errors"] == []
    assert result["commercial_truth"]["wtp"] == "UNKNOWN"
    assert result["commercial_truth"]["recovered_cash"] == "NOT_INFERRED_FROM_THIS_SCORECARD"
    assert len(result["scorecard_sha256"]) == 64


def test_nonclaimable_truth_marks_modeled_claim_as_false_positive():
    result = score_historical_case(
        _alpha_analysis(),
        [GroundTruthLine("LOSS-A1", "NON_CLAIMABLE", "EUR", Decimal("0"))],
        ground_truth_complete=True,
    )
    assert result["false_positive_ids"] == ["LOSS-A1"]
    assert result["false_positive_count"] == 1
    assert result["state_mismatches"][0]["actual"] == "CLAIMABLE"
    assert result["amount_errors"][0]["actual"] == "800.00"
    assert result["absolute_amount_error_by_currency"] == {"EUR": "800.00"}


def test_positive_ground_truth_missing_from_model_is_false_negative():
    result = score_historical_case(
        _alpha_analysis(),
        [
            GroundTruthLine("LOSS-A1", "CLAIMABLE", "EUR", Decimal("800")),
            GroundTruthLine("LOSS-MISSED", "CLAIMABLE", "EUR", Decimal("200")),
        ],
        ground_truth_complete=True,
    )
    assert result["false_negative_ids"] == ["LOSS-MISSED"]
    assert result["missing_modeled_ids"] == ["LOSS-MISSED"]


def test_unexpected_modeled_positive_is_only_fp_when_truth_declared_complete():
    incomplete = score_historical_case(
        _alpha_analysis(),
        [],
        ground_truth_complete=False,
    )
    assert incomplete["unexpected_modeled_ids"] == ["LOSS-A1"]
    assert incomplete["false_positive_count"] == 0

    complete = score_historical_case(
        _alpha_analysis(),
        [],
        ground_truth_complete=True,
    )
    assert complete["false_positive_ids"] == ["LOSS-A1"]


def test_unknown_ground_truth_never_becomes_success_evidence():
    result = score_historical_case(
        _alpha_analysis(),
        [GroundTruthLine("LOSS-A1", "UNKNOWN", "EUR")],
        ground_truth_complete=False,
    )
    assert result["unknown_truth_ids"] == ["LOSS-A1"]
    assert result["false_positive_count"] == 0
    assert result["false_negative_count"] == 0


def test_wtp_is_only_evidenced_when_explicit_evidence_text_is_supplied():
    result = score_historical_case(
        _alpha_analysis(),
        [GroundTruthLine("LOSS-A1", "CLAIMABLE", "EUR", Decimal("800"))],
        ground_truth_complete=True,
        operational_metrics=PilotOperationalMetrics(
            wtp_evidence="Decision maker explicitly accepted paid-pilot price in recorded pilot evidence"
        ),
    )
    assert result["commercial_truth"]["wtp"] == "EVIDENCED"


def test_ground_truth_validation_rejects_invalid_money_and_duplicates():
    with pytest.raises(ValueError, match="GROUND_TRUTH_AMOUNT_INVALID"):
        GroundTruthLine("LOSS-X", "CLAIMABLE", "EUR", Decimal("NaN"))
    with pytest.raises(ValueError, match="NON_CLAIMABLE_EXPECTED_AMOUNT"):
        GroundTruthLine("LOSS-X", "NON_CLAIMABLE", "EUR", Decimal("1"))
    duplicate = GroundTruthLine("LOSS-A1", "CLAIMABLE", "EUR", Decimal("800"))
    with pytest.raises(ValueError, match="DUPLICATE_GROUND_TRUTH_LOSS_ID"):
        score_historical_case(
            _alpha_analysis(),
            [duplicate, duplicate],
            ground_truth_complete=True,
        )
