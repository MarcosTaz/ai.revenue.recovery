from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class QuickCloseoutState(str, Enum):
    ELIGIBLE_FOR_CO_REVIEW = "ELIGIBLE_FOR_CO_REVIEW"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class QuickCloseoutInput:
    contract_id: str
    physically_complete: bool | None
    total_contract_amount: Decimal | None
    unsettled_direct_and_indirect_costs: Decimal | None
    risk_assessment_completed: bool | None
    risk_assessment_supports_use: bool | None
    reasonable_estimate_agreement_reachable: bool | None
    special_recovery_limitation_identified: bool | None
    evidence_complete: bool


@dataclass(frozen=True)
class QuickCloseoutDecision:
    contract_id: str
    state: QuickCloseoutState
    threshold_amount: Decimal | None
    unsettled_cost_ratio: Decimal | None
    explanation: str


def assess_quick_closeout(case: QuickCloseoutInput) -> QuickCloseoutDecision:
    """Deterministic screening gate for FAR 42.708 quick-closeout eligibility.

    This does not bind a contracting officer and does not establish final rates.
    It only screens whether the documented facts satisfy the objective prerequisites
    before a human contracting/legal/accounting review.
    """
    if not case.evidence_complete:
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.UNKNOWN,
            None,
            None,
            "Quick-closeout evidence is incomplete.",
        )

    values = (case.total_contract_amount, case.unsettled_direct_and_indirect_costs)
    if any(value is None for value in values):
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.UNKNOWN,
            None,
            None,
            "Contract amount and unsettled direct/indirect costs are required.",
        )

    total = case.total_contract_amount
    unsettled = case.unsettled_direct_and_indirect_costs
    if (
        not total.is_finite()
        or not unsettled.is_finite()
        or total <= 0
        or unsettled < 0
    ):
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.REQUIRES_REVIEW,
            None,
            None,
            "Invalid economic inputs require qualified review.",
        )

    threshold = min(Decimal("1000000"), total * Decimal("0.10"))
    ratio = unsettled / total

    if case.physically_complete is not True:
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.NOT_ELIGIBLE,
            threshold,
            ratio,
            "Contract is not evidenced as physically complete.",
        )

    if unsettled > threshold:
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.NOT_ELIGIBLE,
            threshold,
            ratio,
            "Unsettled costs exceed the FAR 42.708 materiality threshold.",
        )

    tri_state = (
        case.risk_assessment_completed,
        case.risk_assessment_supports_use,
        case.reasonable_estimate_agreement_reachable,
        case.special_recovery_limitation_identified,
    )
    if any(value is None for value in tri_state):
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.UNKNOWN,
            threshold,
            ratio,
            "Risk assessment, estimate-agreement and special-limitation facts must be evidenced.",
        )

    if not case.risk_assessment_completed or not case.risk_assessment_supports_use:
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.NOT_ELIGIBLE,
            threshold,
            ratio,
            "Required risk assessment does not support quick closeout.",
        )

    if not case.reasonable_estimate_agreement_reachable:
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.NOT_ELIGIBLE,
            threshold,
            ratio,
            "Agreement on a reasonable estimate of allocable dollars is not currently supportable.",
        )

    if case.special_recovery_limitation_identified:
        return QuickCloseoutDecision(
            case.contract_id,
            QuickCloseoutState.REQUIRES_REVIEW,
            threshold,
            ratio,
            "A special contract provision may limit recovery of otherwise allowable indirect costs.",
        )

    return QuickCloseoutDecision(
        case.contract_id,
        QuickCloseoutState.ELIGIBLE_FOR_CO_REVIEW,
        threshold,
        ratio,
        "Objective FAR 42.708 screening criteria are satisfied; contracting-officer review remains required.",
    )
