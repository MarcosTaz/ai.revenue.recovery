from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

_HINTS: dict[str, dict[str, str]] = {
    "MISSING_INVENTORY_OR_COST_RECORD": {
        "proves": "QUANTITY_AND_OR_COST_BASIS_FOR_ECONOMIC_EXPOSURE",
        "holder_hint": "SUPPLIER_FINANCE_INVENTORY_OR_COST_ACCOUNTING",
    },
    "MISSING_OWNERSHIP_EVIDENCE": {
        "proves": "WHETHER_THE_ASSET_OR_EXPOSURE_IS_SUPPLIER_OWNED",
        "holder_hint": "SUPPLIER_ASSET_RECORDS_OR_CUSTOMER_TOOLING_RECORDS",
    },
    "MISSING_MITIGATION_EVIDENCE": {
        "proves": "REUSE_RESALE_SCRAP_CANCELLATION_OR_OTHER_OFFSET",
        "holder_hint": "SUPPLIER_OPERATIONS_PROCUREMENT_OR_FINANCE",
    },
    "MISSING_REIMBURSEMENT_EVIDENCE": {
        "proves": "PRIOR_CREDIT_REIMBURSEMENT_SETTLEMENT_OR_PAYMENT",
        "holder_hint": "SUPPLIER_FINANCE_AR_OR_CUSTOMER_SETTLEMENT_RECORDS",
    },
    "MISSING_CONTRACTUAL_BASIS": {
        "proves": "CONTRACTUAL_OR_COMMERCIAL_BASIS_FOR_RECOVERABILITY",
        "holder_hint": "SUPPLIER_COMMERCIAL_LEGAL_OR_CUSTOMER_PROCUREMENT",
    },
    "MISSING_SUPPORTING_DOCUMENT": {
        "proves": "DOCUMENTARY_SUPPORT_FOR_THE_ENTITLEMENT_INTERPRETATION",
        "holder_hint": "SUPPLIER_COMMERCIAL_LEGAL_OR_CUSTOMER_PROCUREMENT",
    },
    "MISSING_REQUIRED_EVIDENCE_REFERENCE": {
        "proves": "REQUIRED_LINEAGE_SOURCE_FOR_THE_CLAIM_LINE",
        "holder_hint": "UNKNOWN",
    },
}


def _parse_issue(issue: str) -> tuple[str, str | None]:
    if ":" not in issue:
        return issue, None
    code, remainder = issue.split(":", 1)
    return code, remainder or None


def _hint_for(issue: str) -> dict[str, str]:
    code, reference = _parse_issue(issue)
    if code in _HINTS:
        return _HINTS[code]
    if code == "UNREGISTERED_EVIDENCE":
        return {
            "proves": "A_CONCRETE_REGISTERED_SOURCE_EXISTS_FOR_THE_REFERENCED_EVIDENCE",
            "holder_hint": "SOURCE_SYSTEM_OR_DOCUMENT_OWNER",
        }
    if code == "EVIDENCE_NOT_VERIFIED":
        return {
            "proves": "INDEPENDENT_REVIEWER_ACCEPTANCE_OF_THE_REGISTERED_SOURCE",
            "holder_hint": "RECOVERY_RADAR_REVIEW_QUEUE",
        }
    if code == "AMBIGUOUS_REGISTERED_SOURCE":
        return {
            "proves": "WHICH_REGISTERED_DOCUMENT_IS_THE_AUTHORITATIVE_SOURCE",
            "holder_hint": "RECOVERY_RADAR_REVIEW_QUEUE_AND_SOURCE_OWNER",
        }
    if code == "EVIDENCE_SCOPE":
        return {
            "proves": "THE_SOURCE_BELONGS_TO_THE_CORRECT_TENANT_SUPPLIER_CUSTOMER_AND_PROGRAM",
            "holder_hint": "RECOVERY_RADAR_REVIEW_QUEUE_AND_SOURCE_OWNER",
        }
    return {
        "proves": "UNKNOWN_UNTIL_REVIEWED",
        "holder_hint": "UNKNOWN",
    }


def _value_context(line: dict[str, Any]) -> tuple[str | None, str, str | None]:
    currency = line.get("currency")
    pre_gate = line.get("pre_gate_amount")
    if pre_gate is not None:
        return str(pre_gate), "MODELED_AMOUNT_BLOCKED_BY_EVIDENCE_GATE", currency
    net = line.get("net_exposure")
    if net is not None:
        return str(net), "NET_EXPOSURE_UPPER_BOUND_NOT_RECOVERABLE_AMOUNT", currency
    return None, "UNKNOWN", currency


def build_missing_evidence_actions(analysis: dict) -> list[dict[str, Any]]:
    """Turn evidence gaps into line-specific, truth-preserving retrieval actions.

    No obtainability probability is invented. Therefore a numeric value ×
    likelihood priority score remains UNKNOWN until a human or measured process
    supplies that likelihood. Within one currency, higher blocked/value-ceiling
    amounts are sorted first only as a value cue, not as a final priority score.
    """
    actions: list[dict[str, Any]] = []
    for line in analysis.get("claim_lines", []):
        lineage = line.get("lineage", {})
        exposure_id = lineage.get("exposure_id")
        issues = list(line.get("missing_evidence", [])) + list(
            line.get("registered_evidence_issues", [])
        )
        for issue in sorted(set(issues)):
            code, reference = _parse_issue(issue)
            hint = _hint_for(issue)
            value, value_basis, currency = _value_context(line)
            actions.append(
                {
                    "exposure_id": exposure_id,
                    "economic_loss_id": lineage.get("economic_loss_id"),
                    "missing_evidence": issue,
                    "evidence_code": code,
                    "reference": reference,
                    "what_it_would_prove": hint["proves"],
                    "likely_holder_hint": hint["holder_hint"],
                    "can_claim_proceed_without_it": False,
                    "blocked_or_upper_bound_value": value,
                    "value_basis": value_basis,
                    "currency": currency,
                    "obtainability_likelihood": "UNKNOWN",
                    "priority_score_value_x_likelihood": None,
                    "priority_state": "AWAITING_OBTAINABILITY_ESTIMATE",
                }
            )

    def sort_key(action: dict[str, Any]):
        raw = action["blocked_or_upper_bound_value"]
        try:
            amount = Decimal(raw) if raw is not None else Decimal("-1")
        except (InvalidOperation, TypeError):
            amount = Decimal("-1")
        return (action.get("currency") or "", -amount, action.get("exposure_id") or "", action["missing_evidence"])

    return sorted(actions, key=sort_key)
