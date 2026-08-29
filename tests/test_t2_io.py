import hashlib
import json
from decimal import Decimal

import pytest

from recovery_radar.engine import analyze_claim
from recovery_radar.synthetic import alpha_components_fixture
from recovery_radar.t2_io import (
    FORMAT,
    SCORECARD_FORMAT,
    GroundTruthInputError,
    export_scorecard_atomic,
    load_ground_truth,
    score_from_input,
)


def _analysis():
    event, exposures, entitlements, _ = alpha_components_fixture()
    return analyze_claim(event, exposures, entitlements)


def _payload():
    return {
        "format": FORMAT,
        "case_origin": "SYNTHETIC",
        "ground_truth_complete": True,
        "provenance": {
            "authorization_reference": None,
            "source_scope_sha256": None,
            "ground_truth_method": "UNKNOWN",
        },
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


def test_final_scorecard_hash_covers_case_origin_and_validation_metadata(tmp_path):
    source = load_ground_truth(_write(tmp_path, _payload()))
    result = score_from_input(_analysis(), source)
    claimed = result["scorecard_sha256"]
    payload = dict(result)
    del payload["scorecard_sha256"]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert claimed == hashlib.sha256(canonical).hexdigest()
    assert len(result["source_scorecard_sha256"]) == 64


def test_scorecard_export_is_atomic_deterministic_and_manifest_bound(tmp_path):
    source = load_ground_truth(_write(tmp_path, _payload()))
    scorecard = score_from_input(_analysis(), source)
    destination = tmp_path / "out" / "scorecard.json"
    first = export_scorecard_atomic(scorecard, destination)
    first_bytes = destination.read_bytes()
    second = export_scorecard_atomic(scorecard, destination)
    second_bytes = destination.read_bytes()
    assert first_bytes == second_bytes
    assert first["sha256"] == second["sha256"] == hashlib.sha256(first_bytes).hexdigest()
    assert first["scorecard_sha256"] == scorecard["scorecard_sha256"]
    envelope = json.loads(first_bytes.decode("utf-8"))
    assert envelope["format"] == SCORECARD_FORMAT
    assert envelope["scorecard"]["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"


def test_real_case_origin_is_measurement_input_not_terminal_promotion(tmp_path):
    payload = _payload()
    payload["case_origin"] = "REAL_AUTHORIZED_HISTORICAL_CASE"
    source = load_ground_truth(_write(tmp_path, payload))
    result = score_from_input(_analysis(), source)
    assert result["validation_classification"] == "REAL_CASE_MEASUREMENT_INPUT"
    assert result["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"


def test_recorded_authorization_and_scope_hash_never_auto_authorize_or_promote(tmp_path):
    payload = _payload()
    payload["case_origin"] = "SYNTHETIC"
    payload["provenance"] = {
        "authorization_reference": "pilot-authorization-record://CASE-001",
        "source_scope_sha256": "a" * 64,
        "ground_truth_method": "BLIND",
    }
    source = load_ground_truth(_write(tmp_path, payload))
    result = score_from_input(_analysis(), source)
    assert result["validation_classification"] == "NON_REAL_CASE_MEASUREMENT_ONLY"
    assert result["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"
    assert result["provenance"] == {
        "authorization_reference": "pilot-authorization-record://CASE-001",
        "authorization_status": "RECORDED_NOT_INDEPENDENTLY_VERIFIED",
        "source_scope_sha256": "a" * 64,
        "source_scope_hash_status": "CALLER_RECORDED_IDENTITY_ONLY",
        "ground_truth_method": "BLIND",
        "ground_truth_method_status": "RECORDED_NOT_INDEPENDENTLY_VERIFIED",
    }


def test_provenance_changes_final_scorecard_hash(tmp_path):
    first_source = load_ground_truth(_write(tmp_path, _payload()))
    first = score_from_input(_analysis(), first_source)
    payload = _payload()
    payload["provenance"]["authorization_reference"] = "auth://1"
    second_source = load_ground_truth(_write(tmp_path, payload))
    second = score_from_input(_analysis(), second_source)
    assert first["scorecard_sha256"] != second["scorecard_sha256"]


def test_ground_truth_input_rejects_bad_provenance_hash_and_method(tmp_path):
    payload = _payload()
    payload["provenance"]["source_scope_sha256"] = "NOT-A-HASH"
    with pytest.raises(GroundTruthInputError, match="SOURCE_SCOPE_INVALID_SHA256"):
        load_ground_truth(_write(tmp_path, payload))

    payload = _payload()
    payload["provenance"]["ground_truth_method"] = "MAGIC"
    with pytest.raises(GroundTruthInputError, match="GROUND_TRUTH_METHOD_UNSUPPORTED"):
        load_ground_truth(_write(tmp_path, payload))


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