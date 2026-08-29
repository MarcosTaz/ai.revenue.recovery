from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

TruthDisposition = Literal["CLAIMABLE", "REQUIRES_REVIEW", "NON_CLAIMABLE", "UNKNOWN"]
_POSITIVE = {"CLAIMABLE", "REQUIRES_REVIEW"}


@dataclass(frozen=True, slots=True)
class GroundTruthLine:
    economic_loss_id: str
    disposition: TruthDisposition
    currency: str
    expected_amount: Decimal | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.economic_loss_id.strip():
            raise ValueError("GROUND_TRUTH_LOSS_ID_REQUIRED")
        if self.disposition not in {
            "CLAIMABLE",
            "REQUIRES_REVIEW",
            "NON_CLAIMABLE",
            "UNKNOWN",
        }:
            raise ValueError("GROUND_TRUTH_DISPOSITION_INVALID")
        if len(self.currency) != 3 or self.currency.upper() != self.currency:
            raise ValueError("GROUND_TRUTH_CURRENCY_INVALID")
        if self.expected_amount is not None:
            if not self.expected_amount.is_finite() or self.expected_amount < 0:
                raise ValueError("GROUND_TRUTH_AMOUNT_INVALID")
            if self.disposition == "NON_CLAIMABLE" and self.expected_amount != 0:
                raise ValueError("NON_CLAIMABLE_EXPECTED_AMOUNT_MUST_BE_ZERO_OR_NONE")


@dataclass(frozen=True, slots=True)
class PilotOperationalMetrics:
    analyst_preparation_minutes: Decimal | None = None
    reviewer_minutes: Decimal | None = None
    total_time_to_package_minutes: Decimal | None = None
    reviewer_evidence_corrections: int | None = None
    reviewer_entitlement_corrections: int | None = None
    missing_evidence_actions_useful: int | None = None
    missing_evidence_actions_not_useful: int | None = None
    repeat_use_signal: Literal["YES", "NO", "UNKNOWN"] = "UNKNOWN"
    wtp_evidence: str | None = None

    def __post_init__(self) -> None:
        for value in (
            self.analyst_preparation_minutes,
            self.reviewer_minutes,
            self.total_time_to_package_minutes,
        ):
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError("INVALID_TIME_METRIC")
        for value in (
            self.reviewer_evidence_corrections,
            self.reviewer_entitlement_corrections,
            self.missing_evidence_actions_useful,
            self.missing_evidence_actions_not_useful,
        ):
            if value is not None and value < 0:
                raise ValueError("INVALID_COUNT_METRIC")
        if self.wtp_evidence is not None:
            if not isinstance(self.wtp_evidence, str) or not self.wtp_evidence.strip():
                raise ValueError("WTP_EVIDENCE_REFERENCE_INVALID")


def _serialize_decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _modeled_by_loss(analysis: dict) -> dict[str, dict]:
    output: dict[str, dict] = {}
    duplicates: set[str] = set()
    for line in analysis.get("claim_lines", []):
        loss_id = line.get("lineage", {}).get("economic_loss_id")
        if not loss_id:
            continue
        if loss_id in output:
            duplicates.add(loss_id)
        else:
            output[loss_id] = line
    if duplicates:
        raise ValueError(
            "MODELED_DUPLICATE_ECONOMIC_LOSS_IDS:" + ",".join(sorted(duplicates))
        )
    return output


def score_historical_case(
    analysis: dict,
    ground_truth: list[GroundTruthLine] | tuple[GroundTruthLine, ...],
    *,
    ground_truth_complete: bool,
    operational_metrics: PilotOperationalMetrics | None = None,
) -> dict:
    """Compare a gated Recovery Radar analysis to explicit human ground truth.

    The caller must say whether ground truth is exhaustive. Unexpected modeled
    positives are counted as false positives only when the truth set is declared
    complete. UNKNOWN truth lines never become success evidence.

    Commercial observations are deliberately non-self-validating. A string stored
    in ``wtp_evidence`` is only a pointer/note for later independent verification;
    it cannot promote willingness-to-pay to an evidenced state inside this
    scorecard.
    """
    truth_by_loss: dict[str, GroundTruthLine] = {}
    for item in ground_truth:
        if item.economic_loss_id in truth_by_loss:
            raise ValueError(f"DUPLICATE_GROUND_TRUTH_LOSS_ID:{item.economic_loss_id}")
        truth_by_loss[item.economic_loss_id] = item

    modeled = _modeled_by_loss(analysis)
    false_positive_ids: list[str] = []
    false_negative_ids: list[str] = []
    state_mismatches: list[dict] = []
    currency_mismatches: list[dict] = []
    amount_errors: list[dict] = []
    unknown_truth_ids: list[str] = []
    missing_modeled_ids: list[str] = []

    for loss_id, truth in sorted(truth_by_loss.items()):
        line = modeled.get(loss_id)
        if truth.disposition == "UNKNOWN":
            unknown_truth_ids.append(loss_id)
            continue
        if line is None:
            missing_modeled_ids.append(loss_id)
            if truth.disposition in _POSITIVE:
                false_negative_ids.append(loss_id)
            continue

        modeled_state = line.get("state") or "UNKNOWN"
        modeled_positive = modeled_state in _POSITIVE
        truth_positive = truth.disposition in _POSITIVE
        if truth_positive and not modeled_positive:
            false_negative_ids.append(loss_id)
        elif not truth_positive and modeled_positive:
            false_positive_ids.append(loss_id)

        if modeled_state != truth.disposition:
            state_mismatches.append(
                {
                    "economic_loss_id": loss_id,
                    "expected": truth.disposition,
                    "actual": modeled_state,
                }
            )

        modeled_currency = line.get("currency")
        if modeled_currency != truth.currency:
            currency_mismatches.append(
                {
                    "economic_loss_id": loss_id,
                    "expected": truth.currency,
                    "actual": modeled_currency,
                }
            )

        modeled_amount_raw = line.get("claimable_amount")
        if truth.expected_amount is not None:
            modeled_amount = (
                Decimal(str(modeled_amount_raw))
                if modeled_amount_raw is not None
                else None
            )
            error = (
                None
                if modeled_amount is None
                else modeled_amount - truth.expected_amount
            )
            if modeled_amount != truth.expected_amount:
                amount_errors.append(
                    {
                        "economic_loss_id": loss_id,
                        "currency": truth.currency,
                        "expected": str(truth.expected_amount),
                        "actual": _serialize_decimal(modeled_amount),
                        "signed_error": _serialize_decimal(error),
                    }
                )

    unexpected_modeled_ids = sorted(set(modeled) - set(truth_by_loss))
    if ground_truth_complete:
        for loss_id in unexpected_modeled_ids:
            if modeled[loss_id].get("state") in _POSITIVE:
                false_positive_ids.append(loss_id)

    amount_abs_error_by_currency: dict[str, Decimal] = {}
    for item in amount_errors:
        if item["signed_error"] is None:
            continue
        currency = item["currency"]
        amount_abs_error_by_currency[currency] = (
            amount_abs_error_by_currency.get(currency, Decimal("0"))
            + abs(Decimal(item["signed_error"]))
        )

    metrics = operational_metrics or PilotOperationalMetrics()
    metrics_payload = {
        "analyst_preparation_minutes": _serialize_decimal(metrics.analyst_preparation_minutes),
        "reviewer_minutes": _serialize_decimal(metrics.reviewer_minutes),
        "total_time_to_package_minutes": _serialize_decimal(metrics.total_time_to_package_minutes),
        "reviewer_evidence_corrections": metrics.reviewer_evidence_corrections,
        "reviewer_entitlement_corrections": metrics.reviewer_entitlement_corrections,
        "missing_evidence_actions_useful": metrics.missing_evidence_actions_useful,
        "missing_evidence_actions_not_useful": metrics.missing_evidence_actions_not_useful,
        "repeat_use_signal": metrics.repeat_use_signal,
        "wtp_evidence_reference": metrics.wtp_evidence,
        "wtp_evidence_status": (
            "RECORDED_NOT_INDEPENDENTLY_VERIFIED"
            if metrics.wtp_evidence
            else "NOT_RECORDED"
        ),
    }

    result = {
        "ground_truth_complete": ground_truth_complete,
        "ground_truth_line_count": len(truth_by_loss),
        "modeled_line_count": len(modeled),
        "false_positive_ids": sorted(set(false_positive_ids)),
        "false_negative_ids": sorted(set(false_negative_ids)),
        "false_positive_count": len(set(false_positive_ids)),
        "false_negative_count": len(set(false_negative_ids)),
        "state_mismatches": state_mismatches,
        "currency_mismatches": currency_mismatches,
        "amount_errors": amount_errors,
        "absolute_amount_error_by_currency": {
            currency: str(value)
            for currency, value in sorted(amount_abs_error_by_currency.items())
        },
        "unknown_truth_ids": unknown_truth_ids,
        "missing_modeled_ids": missing_modeled_ids,
        "unexpected_modeled_ids": unexpected_modeled_ids,
        "operational_metrics": metrics_payload,
        "commercial_truth": {
            "wtp": "UNKNOWN_EXTERNAL",
            "wtp_reference_status": metrics_payload["wtp_evidence_status"],
            "recovered_cash": "NOT_INFERRED_FROM_THIS_SCORECARD",
            "customer_acceptance": "NOT_INFERRED_FROM_THIS_SCORECARD",
        },
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["scorecard_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result
