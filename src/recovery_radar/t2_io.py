from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .t2_validation import GroundTruthLine, PilotOperationalMetrics, score_historical_case

FORMAT = "RECOVERY_RADAR_GROUND_TRUTH_V1"
MAX_BYTES = 5 * 1024 * 1024
_CASE_ORIGINS = {"REAL_AUTHORIZED_HISTORICAL_CASE", "SYNTHETIC", "UNKNOWN"}


class GroundTruthInputError(ValueError):
    pass


def _decimal(value, name):
    if value is None:
        return None
    if isinstance(value, bool):
        raise GroundTruthInputError(f"{name}_INVALID_DECIMAL")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise GroundTruthInputError(f"{name}_INVALID_DECIMAL") from None
    if not result.is_finite():
        raise GroundTruthInputError(f"{name}_NON_FINITE")
    return result


def load_ground_truth(path: str | Path) -> dict:
    source = Path(path)
    if not source.is_file():
        raise GroundTruthInputError("GROUND_TRUTH_FILE_NOT_FOUND")
    if source.stat().st_size > MAX_BYTES:
        raise GroundTruthInputError("GROUND_TRUTH_FILE_TOO_LARGE")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GroundTruthInputError("GROUND_TRUTH_INVALID_JSON_UTF8") from exc
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise GroundTruthInputError("GROUND_TRUTH_FORMAT_UNSUPPORTED")
    if not isinstance(data.get("ground_truth_complete"), bool):
        raise GroundTruthInputError("GROUND_TRUTH_COMPLETE_MUST_BE_BOOLEAN")
    origin = data.get("case_origin")
    if origin not in _CASE_ORIGINS:
        raise GroundTruthInputError(f"CASE_ORIGIN_UNSUPPORTED:{origin}")
    raw_lines = data.get("lines")
    if not isinstance(raw_lines, list) or len(raw_lines) > 10_000:
        raise GroundTruthInputError("GROUND_TRUTH_LINES_INVALID")
    lines = []
    for item in raw_lines:
        if not isinstance(item, dict):
            raise GroundTruthInputError("GROUND_TRUTH_LINE_MUST_BE_OBJECT")
        try:
            lines.append(
                GroundTruthLine(
                    str(item["economic_loss_id"]),
                    str(item["disposition"]),
                    str(item["currency"]),
                    _decimal(item.get("expected_amount"), "EXPECTED_AMOUNT"),
                    str(item.get("note", "")),
                )
            )
        except KeyError as exc:
            raise GroundTruthInputError(f"GROUND_TRUTH_FIELD_REQUIRED:{exc.args[0]}") from None
    metrics = data.get("operational_metrics", {})
    if not isinstance(metrics, dict):
        raise GroundTruthInputError("OPERATIONAL_METRICS_MUST_BE_OBJECT")
    repeat = metrics.get("repeat_use_signal", "UNKNOWN")
    if repeat not in {"YES", "NO", "UNKNOWN"}:
        raise GroundTruthInputError(f"REPEAT_USE_SIGNAL_UNSUPPORTED:{repeat}")
    operational = PilotOperationalMetrics(
        analyst_preparation_minutes=_decimal(metrics.get("analyst_preparation_minutes"), "ANALYST_PREPARATION_MINUTES"),
        reviewer_minutes=_decimal(metrics.get("reviewer_minutes"), "REVIEWER_MINUTES"),
        total_time_to_package_minutes=_decimal(metrics.get("total_time_to_package_minutes"), "TOTAL_TIME_TO_PACKAGE_MINUTES"),
        reviewer_evidence_corrections=metrics.get("reviewer_evidence_corrections"),
        reviewer_entitlement_corrections=metrics.get("reviewer_entitlement_corrections"),
        missing_evidence_actions_useful=metrics.get("missing_evidence_actions_useful"),
        missing_evidence_actions_not_useful=metrics.get("missing_evidence_actions_not_useful"),
        repeat_use_signal=repeat,
        wtp_evidence=metrics.get("wtp_evidence_reference"),
    )
    return {
        "case_origin": origin,
        "complete": data["ground_truth_complete"],
        "lines": tuple(lines),
        "metrics": operational,
    }


def score_from_input(analysis: dict, source: dict) -> dict:
    result = score_historical_case(
        analysis,
        source["lines"],
        ground_truth_complete=source["complete"],
        operational_metrics=source["metrics"],
    )
    result["case_origin"] = source["case_origin"]
    result["validation_classification"] = (
        "REAL_CASE_MEASUREMENT_INPUT"
        if source["case_origin"] == "REAL_AUTHORIZED_HISTORICAL_CASE"
        else "NON_REAL_CASE_MEASUREMENT_ONLY"
    )
    result["terminal_promotion"] = "NOT_INFERRED_FROM_SCORECARD"
    return result
