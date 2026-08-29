from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from .engine import FindingState, SupportState, money


class AllowabilityState(str, Enum):
    SUPPORTED_ALLOWABLE = "SUPPORTED_ALLOWABLE"
    SUPPORTED_UNALLOWABLE = "SUPPORTED_UNALLOWABLE"
    CONTRACT_SPECIFIC = "CONTRACT_SPECIFIC"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class ContractBillability(str, Enum):
    BILLABLE = "BILLABLE"
    NOT_BILLABLE = "NOT_BILLABLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DirectCostInput:
    contract_id: str
    transaction_id: str
    amount: Decimal
    billed_amount: Decimal
    allowability: AllowabilityState
    allocability: SupportState
    contract_billability: ContractBillability
    duplicate: bool = False
    remaining_cost_ceiling: Optional[Decimal] = None
    remaining_funding: Optional[Decimal] = None


@dataclass(frozen=True)
class DirectCostResult:
    contract_id: str
    transaction_id: str
    expected_billable: Optional[Decimal]
    billed_amount: Decimal
    variance: Optional[Decimal]
    state: FindingState
    explanation: str


def compute_direct_cost_variance(case: DirectCostInput) -> DirectCostResult:
    billed = money(case.billed_amount)

    if case.duplicate:
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            Decimal("0.00"),
            billed,
            None,
            FindingState.NO_VARIANCE,
            "Duplicate transaction excluded from entitlement calculation.",
        )

    if case.allowability == AllowabilityState.SUPPORTED_UNALLOWABLE:
        variance = money(Decimal("0") - billed)
        state = FindingState.PAYABLE_CANDIDATE if variance < 0 else FindingState.NO_VARIANCE
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            Decimal("0.00"),
            billed,
            variance,
            state,
            "Cost is supported as unallowable and cannot create a recovery candidate.",
        )

    if case.allowability in {AllowabilityState.UNKNOWN, AllowabilityState.INSUFFICIENT_EVIDENCE}:
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            None,
            billed,
            None,
            FindingState.UNKNOWN,
            "Allowability is not sufficiently evidenced.",
        )

    if case.allowability != AllowabilityState.SUPPORTED_ALLOWABLE:
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            None,
            billed,
            None,
            FindingState.REQUIRES_REVIEW,
            "Allowability requires qualified or contract-specific review.",
        )

    if case.allocability != SupportState.SUPPORTED:
        state = (
            FindingState.UNKNOWN
            if case.allocability in {SupportState.UNKNOWN, SupportState.INSUFFICIENT_EVIDENCE}
            else FindingState.REQUIRES_REVIEW
        )
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            None,
            billed,
            None,
            state,
            "Allocability is not fully supported.",
        )

    if case.contract_billability == ContractBillability.NOT_BILLABLE:
        variance = money(Decimal("0") - billed)
        state = FindingState.PAYABLE_CANDIDATE if variance < 0 else FindingState.NO_VARIANCE
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            Decimal("0.00"),
            billed,
            variance,
            state,
            "Contract terms do not permit billing this cost.",
        )

    if case.contract_billability == ContractBillability.UNKNOWN:
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            None,
            billed,
            None,
            FindingState.UNKNOWN,
            "Contract billability is unknown.",
        )

    if case.contract_billability == ContractBillability.REQUIRES_REVIEW:
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            None,
            billed,
            None,
            FindingState.REQUIRES_REVIEW,
            "Contract billability requires qualified review.",
        )

    expected = money(case.amount)
    if case.remaining_cost_ceiling is not None:
        expected = min(expected, money(case.remaining_cost_ceiling))

    variance = money(expected - billed)
    if variance > 0 and case.remaining_funding is not None and variance > money(case.remaining_funding):
        return DirectCostResult(
            case.contract_id,
            case.transaction_id,
            expected,
            billed,
            variance,
            FindingState.REQUIRES_REVIEW,
            "Positive variance exceeds verified remaining funding.",
        )

    if variance > 0:
        state = FindingState.RECOVERY_CANDIDATE
        explanation = "Supported allowable, allocable and contract-billable direct cost exceeds prior billing."
    elif variance < 0:
        state = FindingState.PAYABLE_CANDIDATE
        explanation = "Prior billing exceeds supported billable direct cost."
    else:
        state = FindingState.NO_VARIANCE
        explanation = "Supported billable direct cost is fully reflected in prior billing."

    return DirectCostResult(case.contract_id, case.transaction_id, expected, billed, variance, state, explanation)


@dataclass(frozen=True)
class PaymentInput:
    invoice_id: str
    verified_invoice_amount: Decimal
    paid_amount: Decimal
    invoice_supported: bool
    payment_evidence_supported: bool
    disputed_or_withheld: bool = False


def compute_payment_shortfall(case: PaymentInput):
    if not case.invoice_supported or not case.payment_evidence_supported:
        return {
            "invoice_id": case.invoice_id,
            "state": FindingState.UNKNOWN,
            "variance": None,
            "explanation": "Invoice or payment evidence is incomplete.",
        }

    variance = money(case.verified_invoice_amount - case.paid_amount)
    if variance > 0 and case.disputed_or_withheld:
        state = FindingState.REQUIRES_REVIEW
        explanation = "Verified payment shortfall exists but is disputed or withheld."
    elif variance > 0:
        state = FindingState.RECOVERY_CANDIDATE
        explanation = "Verified invoice exceeds supported payments received."
    elif variance < 0:
        state = FindingState.PAYABLE_CANDIDATE
        explanation = "Supported payments exceed the verified invoice amount."
    else:
        state = FindingState.NO_VARIANCE
        explanation = "Verified invoice is fully paid."

    return {
        "invoice_id": case.invoice_id,
        "state": state,
        "variance": variance,
        "explanation": explanation,
    }
