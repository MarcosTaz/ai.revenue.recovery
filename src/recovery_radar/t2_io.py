from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .t2_validation import GroundTruthLine, PilotOperationalMetrics, score_historical_case

FORMAT = "RECOVERY_RADAR_GROUND_TRUTH_V1"
MAX_BYTES = 5 * 1024 * 1024
_CASE_ORIGINS = {"REAL_AUTHORIZED_HISTORICAL_CASE", "SYNTHETIC", "UNKNOWN"}


class GroundTruthInputError(ValueError):
    pass


def _text(value, name, *, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise GroundTruthInputError(f"{name}_REQUIRED")
    return value.strip()


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


def _count(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GroundTruthInputError(f"{name}_INVALID_NONNEGATIVE_INTEGER")
    return value


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
        lines.append(
            GroundTruthLine(
                _text(item.get("economic_loss_id"), "ECONOMIC_LOSS_ID"),
                _text(item.get("disposition"), "DISPOSITION"),
                _text(item.get("currency"), "CURRENCY"),
                _decimal(item.get("expected_amount"), "EXPECTED_AMOUNT"),
                _text(item.get("note"), "NOTE", optional=True) or "",
            )
        )
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
        reviewer_evidence_corrections=_count(metrics.get("reviewer_evidence_corrections"), "REVIEWER_EVIDENCE_CORRECTIONS"),
        reviewer_entitlement_corrections=_count(metrics.get("reviewer_entitlement_corrections"), "REVIEWER_ENTITLEMENT_CORRECTIONS"),
        missing_evidence_actions_useful=_count(metrics.get("missing_evidence_actions_useful"), "MISSING_EVIDENCE_ACTIONS_USEFUL"),
        missing_evidence_actions_not_useful=_count(metrics.get("missing_evidence_actions_not_useful"), "MISSING_EVIDENCE_ACTIONS_NOT_USEFUL"),
        repeat_use_signal=repeat,
        wtp_evidence=_text(metrics.get("wtp_evidence_reference"), "WTP_EVIDENCE_REFERENCE", optional=True),
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
    result["source_scorecard_sha256"] = result.pop("scorecard_sha256")
    result["case_origin"] = source["case_origin"]
    result["validation_classification"] = (
        "REAL_CASE_MEASUREMENT_INPUT"
        if source["case_origin"] == "REAL_AUTHORIZED_HISTORICAL_CASE"
        else "NON_REAL_CASE_MEASUREMENT_ONLY"
    )
    result["terminal_promotion"] = "NOT_INFERRED_FROM_SCORECARD"
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result["scorecard_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result
