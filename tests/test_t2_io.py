import json
from decimal import Decimal

import pytest

from recovery_radar.engine import analyze_claim
from recovery_radar.synthetic import alpha_components_fixture
from recovery_radar.t2_io import FORMAT, GroundTruthInputError, load_ground_truth, score_from_input


def _analysis():
    event, exposures, entitlements, _ = alpha_components_fixture()
    return analyze_claim(event, exposures, entitlements)


def _payload():
    return {
        "format": FORMAT,
        "case_origin": "SYNTHETIC",
        "ground_truth_complete": True,
        "lines": [
            {
                "economic_loss_id": "LOSS-A1",
                "disposition": "CLAIMABLE",
                "currency": "EUR",
                "expected_amount": "800.00",
            }
        ],
        "operational_metrics": {
            "analyst_preparation_minutes": "30",
            "reviewer_minutes": "10",
            "reviewer_evidence_corrections": 1,
            "repeat_use_signal": "YES",
            "wtp_evidence_reference": "synthetic note must not validate WTP",
        },
    }


def _write(tmp_path, payload):
    path = tmp_path / "ground-truth.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_synthetic_scorecard_never_promotes_t2_or_wtp(tmp_path):
    source = load_ground_truth(_write(tmp_path, _payload()))
    result = score_from_input(_analysis(), source)
    assert result["false_positive_count"] == 0
    assert result["false_negative_count"] == 0
    assert result["case_origin"] == "SYNTHETIC"
    assert result["validation_classification"] == "NON_REAL_CASE_MEASUREMENT_ONLY"
    assert result["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"
    assert result["commercial_truth"]["wtp"] == "UNKNOWN_EXTERNAL"
    assert result["operational_metrics"]["wtp_evidence_status"] == "RECORDED_NOT_INDEPENDENTLY_VERIFIED"


def test_real_case_origin_is_measurement_input_not_terminal_promotion(tmp_path):
    payload = _payload()
    payload["case_origin"] = "REAL_AUTHORIZED_HISTORICAL_CASE"
    source = load_ground_truth(_write(tmp_path, payload))
    result = score_from_input(_analysis(), source)
    assert result["validation_classification"] == "REAL_CASE_MEASUREMENT_INPUT"
    assert result["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"


def test_ground_truth_input_rejects_nonboolean_complete_and_nonfinite_money(tmp_path):
    payload = _payload()
    payload["ground_truth_complete"] = "true"
    with pytest.raises(GroundTruthInputError, match="GROUND_TRUTH_COMPLETE_MUST_BE_BOOLEAN"):
        load_ground_truth(_write(tmp_path, payload))

    payload = _payload()
    payload["lines"][0]["expected_amount"] = "NaN"
    with pytest.raises(GroundTruthInputError, match="EXPECTED_AMOUNT_NON_FINITE"):
        load_ground_truth(_write(tmp_path, payload))


def test_ground_truth_input_rejects_missing_identity_and_bad_count_type(tmp_path):
    payload = _payload()
    del payload["lines"][0]["economic_loss_id"]
    with pytest.raises(GroundTruthInputError, match="ECONOMIC_LOSS_ID_REQUIRED"):
        load_ground_truth(_write(tmp_path, payload))

    payload = _payload()
    payload["operational_metrics"]["reviewer_evidence_corrections"] = "1"
    with pytest.raises(GroundTruthInputError, match="REVIEWER_EVIDENCE_CORRECTIONS_INVALID_NONNEGATIVE_INTEGER"):
        load_ground_truth(_write(tmp_path, payload))


def test_ground_truth_line_amount_remains_decimal(tmp_path):
    source = load_ground_truth(_write(tmp_path, _payload()))
    assert source["lines"][0].expected_amount == Decimal("800.00")
