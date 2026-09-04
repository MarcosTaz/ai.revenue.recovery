from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .engine import money


class AssuranceState(str, Enum):
    CURRENT = "CURRENT"
    SUPPORTED_UNBILLED = "SUPPORTED_UNBILLED"
    PAYMENT_SHORTFALL = "PAYMENT_SHORTFALL"
    PAYABLE_EXPOSURE = "PAYABLE_EXPOSURE"
    AT_RISK = "AT_RISK"
    NOT_ALLOWABLE = "NOT_ALLOWABLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ContractAssuranceInput:
    contract_id: str
    supported_expected_billing: Decimal | None
    cumulative_billed: Decimal | None
    cumulative_paid: Decimal | None
    evidence_complete: bool
    contract_terms_supported: bool
    allowability_supported: bool
    allocability_supported: bool
    funding_supported: bool
    ceiling_supported: bool
    final_rate_settled_when_required: bool
    expressly_unallowable: bool = False
    procedural_risk: bool = False


@dataclass(frozen=True)
class ContractAssuranceSnapshot:
    contract_id: str
    state: AssuranceState
    earned_supported: Decimal | None
    billed: Decimal | None
    paid: Decimal | None
    supported_unbilled: Decimal | None
    payment_shortfall: Decimal | None
    payable_exposure: Decimal | None
    explanation: str


def _valid_amount(value: Decimal | None) -> bool:
    return value is None or (value.is_finite() and value >= 0)


def compute_contract_assurance(case: ContractAssuranceInput) -> ContractAssuranceSnapshot:
    values = (case.supported_expected_billing, case.cumulative_billed, case.cumulative_paid)
    if not all(_valid_amount(value) for value in values):
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.REQUIRES_REVIEW,
            None, None, None, None, None, None,
            "Negative or non-finite economic inputs require review.",
        )
    if case.expressly_unallowable:
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.NOT_ALLOWABLE,
            None,
            None if case.cumulative_billed is None else money(case.cumulative_billed),
            None if case.cumulative_paid is None else money(case.cumulative_paid),
            None, None, None,
            "An expressly unallowable item cannot become supported earned revenue.",
        )
    if not case.evidence_complete or case.supported_expected_billing is None or case.cumulative_billed is None:
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.UNKNOWN,
            None, None, None, None, None, None,
            "Expected economics and cumulative billing require complete evidence.",
        )
    if not all((
        case.contract_terms_supported,
        case.allowability_supported,
        case.allocability_supported,
        case.final_rate_settled_when_required,
    )):
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.REQUIRES_REVIEW,
            money(case.supported_expected_billing), money(case.cumulative_billed),
            None if case.cumulative_paid is None else money(case.cumulative_paid),
            None, None, None,
            "Contract, cost or final-rate prerequisites are not fully supported.",
        )

    earned = money(case.supported_expected_billing)
    billed = money(case.cumulative_billed)
    paid = None if case.cumulative_paid is None else money(case.cumulative_paid)

    if not case.funding_supported or not case.ceiling_supported or case.procedural_risk:
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.AT_RISK,
            earned, billed, paid, None, None, None,
            "Economic variance exists in a funding, ceiling or procedural risk context and is not promoted to supported unbilled revenue.",
        )

    if billed > earned:
        payable = money(billed - earned)
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.PAYABLE_EXPOSURE,
            earned, billed, paid, None, None, payable,
            "Cumulative billing exceeds the supported expected economics.",
        )

    unbilled = money(earned - billed)
    if unbilled > 0:
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.SUPPORTED_UNBILLED,
            earned, billed, paid, unbilled, None, None,
            "Supported expected economics exceed cumulative billing after current deterministic gates.",
        )

    if paid is None:
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.UNKNOWN,
            earned, billed, None, Decimal("0.00"), None, None,
            "Billing is current but payment evidence is incomplete.",
        )
    if paid < billed:
        shortfall = money(billed - paid)
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.PAYMENT_SHORTFALL,
            earned, billed, paid, Decimal("0.00"), shortfall, None,
            "Verified payments are below supported cumulative billing.",
        )
    if paid > billed:
        return ContractAssuranceSnapshot(
            case.contract_id, AssuranceState.REQUIRES_REVIEW,
            earned, billed, paid, Decimal("0.00"), None, money(paid - billed),
            "Verified payments exceed cumulative billing and require cash-application/refund review.",
        )
    return ContractAssuranceSnapshot(
        case.contract_id, AssuranceState.CURRENT,
        earned, billed, paid, Decimal("0.00"), Decimal("0.00"), Decimal("0.00"),
        "Supported expected economics, cumulative billing and verified payment are aligned.",
    )
