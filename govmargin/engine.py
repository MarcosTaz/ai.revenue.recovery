from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional


CENT = Decimal("0.01")


class SupportState(str, Enum):
    SUPPORTED = "SUPPORTED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class RateState(str, Enum):
    SETTLED_FINAL = "SETTLED_FINAL"
    PROPOSED_FINAL = "PROPOSED_FINAL"
    PROVISIONAL = "PROVISIONAL"
    UNKNOWN = "UNKNOWN"


class FindingState(str, Enum):
    RECOVERY_CANDIDATE = "RECOVERY_CANDIDATE"
    PAYABLE_CANDIDATE = "PAYABLE_CANDIDATE"
    NO_VARIANCE = "NO_VARIANCE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class IndirectTrueUpInput:
    contract_id: str
    period: str
    allocation_base: Decimal
    final_rate: Decimal
    billed_indirect: Decimal
    rate_state: RateState
    contract_terms: SupportState
    base_allowability: SupportState
    base_allocability: SupportState
    indirect_ceiling_amount: Optional[Decimal] = None
    remaining_funding: Optional[Decimal] = None


@dataclass(frozen=True)
class IndirectTrueUpResult:
    contract_id: str
    period: str
    expected_indirect: Optional[Decimal]
    billed_indirect: Decimal
    variance: Optional[Decimal]
    state: FindingState
    explanation: str


def compute_indirect_true_up(case: IndirectTrueUpInput) -> IndirectTrueUpResult:
    if case.contract_terms in {SupportState.UNKNOWN, SupportState.INSUFFICIENT_EVIDENCE}:
        return IndirectTrueUpResult(
            case.contract_id,
            case.period,
            None,
            money(case.billed_indirect),
            None,
            FindingState.UNKNOWN,
            "Contract applicability or terms are not sufficiently evidenced.",
        )

    if case.contract_terms == SupportState.REQUIRES_REVIEW:
        return IndirectTrueUpResult(
            case.contract_id,
            case.period,
            None,
            money(case.billed_indirect),
            None,
            FindingState.REQUIRES_REVIEW,
            "Contract terms require qualified review before economic entitlement is computed.",
        )

    if case.rate_state != RateState.SETTLED_FINAL:
        return IndirectTrueUpResult(
            case.contract_id,
            case.period,
            None,
            money(case.billed_indirect),
            None,
            FindingState.REQUIRES_REVIEW,
            "A non-settled rate cannot create a verified recovery finding.",
        )

    if case.base_allowability != SupportState.SUPPORTED or case.base_allocability != SupportState.SUPPORTED:
        return IndirectTrueUpResult(
            case.contract_id,
            case.period,
            None,
            money(case.billed_indirect),
            None,
            FindingState.REQUIRES_REVIEW,
            "Allocation base must be supported as allowable and allocable.",
        )

    expected = money(case.allocation_base * case.final_rate)
    if case.indirect_ceiling_amount is not None and expected > case.indirect_ceiling_amount:
        expected = money(case.indirect_ceiling_amount)

    billed = money(case.billed_indirect)
    variance = money(expected - billed)

    if variance > 0 and case.remaining_funding is not None and variance > money(case.remaining_funding):
        return IndirectTrueUpResult(
            case.contract_id,
            case.period,
            expected,
            billed,
            variance,
            FindingState.REQUIRES_REVIEW,
            "Positive variance exceeds verified remaining funding; entitlement cannot be asserted automatically.",
        )

    if variance > 0:
        state = FindingState.RECOVERY_CANDIDATE
        explanation = "Settled final-rate economics exceed cumulative indirect billings."
    elif variance < 0:
        state = FindingState.PAYABLE_CANDIDATE
        explanation = "Cumulative indirect billings exceed the settled final-rate amount."
    else:
        state = FindingState.NO_VARIANCE
        explanation = "Cumulative indirect billings match the settled final-rate amount."

    return IndirectTrueUpResult(
        case.contract_id,
        case.period,
        expected,
        billed,
        variance,
        state,
        explanation,
    )
