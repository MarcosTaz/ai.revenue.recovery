from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class FundingClause(str, Enum):
    LIMITATION_OF_COST = "52.232-20"
    LIMITATION_OF_FUNDS = "52.232-22"


class FundingState(str, Enum):
    WITHIN_VERIFIED_LIMIT = "WITHIN_VERIFIED_LIMIT"
    NOTICE_THRESHOLD_REACHED = "NOTICE_THRESHOLD_REACHED"
    EXCESS_COST_REVIEW_REQUIRED = "EXCESS_COST_REVIEW_REQUIRED"
    FUNDING_EXHAUSTED_REVIEW_REQUIRED = "FUNDING_EXHAUSTED_REVIEW_REQUIRED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FundingSafeguardInput:
    clause: FundingClause | None
    costs_incurred: Decimal | None
    expected_next_notice_window_costs: Decimal | None
    estimated_cost: Decimal | None = None
    allotted_funds: Decimal | None = None
    notice_threshold_percent: Decimal = Decimal("0.75")
    notice_window_days: int = 60
    contracting_officer_increase_evidenced: bool = False


@dataclass(frozen=True)
class FundingSafeguardResult:
    state: FundingState
    verified_limit: Decimal | None
    projected_cost_at_notice_window: Decimal | None
    threshold_amount: Decimal | None
    automatic_recovery_allowed: bool
    explanation: str
    source_rule: str | None


def _nonnegative(value: Decimal | None) -> bool:
    return value is None or (value.is_finite() and value >= 0)


def _valid_threshold(value: Decimal) -> bool:
    return value.is_finite() and Decimal("0.75") <= value <= Decimal("0.85")


def evaluate_funding_safeguard(case: FundingSafeguardInput) -> FundingSafeguardResult:
    """Evaluate funding exposure without creating a reimbursement entitlement.

    FAR 52.232-20 applies to the estimated-cost limit for fully funded
    cost-reimbursement work. FAR 52.232-22 applies to the amount actually allotted
    for incrementally funded cost-reimbursement work. The clauses permit the
    notice window and threshold percentage to vary; unsupported values fail closed.
    """
    if case.clause is None:
        return FundingSafeguardResult(
            FundingState.UNKNOWN, None, None, None, False,
            "No supported funding clause is evidenced.", None,
        )
    values = (
        case.costs_incurred,
        case.expected_next_notice_window_costs,
        case.estimated_cost,
        case.allotted_funds,
    )
    if not all(_nonnegative(value) for value in values):
        return FundingSafeguardResult(
            FundingState.REQUIRES_REVIEW, None, None, None, False,
            "Negative or non-finite funding inputs require qualified review.", case.clause.value,
        )
    if not _valid_threshold(case.notice_threshold_percent) or not 30 <= case.notice_window_days <= 90:
        return FundingSafeguardResult(
            FundingState.REQUIRES_REVIEW, None, None, None, False,
            "Notice threshold/window is outside the clause's supported configurable range.", case.clause.value,
        )
    if case.costs_incurred is None or case.expected_next_notice_window_costs is None:
        return FundingSafeguardResult(
            FundingState.UNKNOWN, None, None, None, False,
            "Current and notice-window projected costs must be evidenced.", case.clause.value,
        )

    if case.clause is FundingClause.LIMITATION_OF_COST:
        limit = case.estimated_cost
        if limit is None:
            return FundingSafeguardResult(
                FundingState.UNKNOWN, None, None, None, False,
                "52.232-20 requires the schedule estimated cost to evaluate the safeguard.", case.clause.value,
            )
    elif case.clause is FundingClause.LIMITATION_OF_FUNDS:
        limit = case.allotted_funds
        if limit is None:
            return FundingSafeguardResult(
                FundingState.UNKNOWN, None, None, None, False,
                "52.232-22 requires the amount actually allotted to evaluate the safeguard.", case.clause.value,
            )
    else:
        return FundingSafeguardResult(
            FundingState.UNKNOWN, None, None, None, False,
            "Funding clause is not recognized by the current safeguard engine.", None,
        )

    projected = case.costs_incurred + case.expected_next_notice_window_costs
    threshold = limit * case.notice_threshold_percent

    if case.costs_incurred > limit:
        state = (
            FundingState.EXCESS_COST_REVIEW_REQUIRED
            if case.clause is FundingClause.LIMITATION_OF_COST
            else FundingState.FUNDING_EXHAUSTED_REVIEW_REQUIRED
        )
        return FundingSafeguardResult(
            state, limit, projected, threshold, False,
            "Costs exceed the evidenced contractual cost/funding limit. This is a review condition, not an automatic recovery right; written Contracting Officer action may be material.",
            case.clause.value,
        )

    if projected > limit:
        return FundingSafeguardResult(
            FundingState.NOTICE_THRESHOLD_REACHED, limit, projected, threshold, False,
            "Projected costs cross the evidenced cost/funding limit within the notice window; notification and funding/estimated-cost review are required before any recovery assertion.",
            case.clause.value,
        )

    if projected >= threshold:
        return FundingSafeguardResult(
            FundingState.NOTICE_THRESHOLD_REACHED, limit, projected, threshold, False,
            "Projected costs meet the evidenced notice threshold; preserve written notice evidence and do not infer additional funding or reimbursement.",
            case.clause.value,
        )

    return FundingSafeguardResult(
        FundingState.WITHIN_VERIFIED_LIMIT, limit, projected, threshold, False,
        "Current plus projected notice-window costs remain below the evidenced notice threshold.",
        case.clause.value,
    )
