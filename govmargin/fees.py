from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from .engine import FindingState, money


class FeeMethod(str, Enum):
    FIXED_AMOUNT = "FIXED_AMOUNT"
    PERCENT_OF_SUPPORTED_COST = "PERCENT_OF_SUPPORTED_COST"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FeeInput:
    contract_id: str
    method: FeeMethod
    fee_terms_supported: bool
    billed_fee: Decimal
    fixed_fee_amount: Optional[Decimal] = None
    supported_cost: Optional[Decimal] = None
    fee_rate: Optional[Decimal] = None
    fee_ceiling: Optional[Decimal] = None


def compute_fee_variance(case: FeeInput):
    if not case.fee_terms_supported or case.method == FeeMethod.UNKNOWN:
        return {"state": FindingState.UNKNOWN, "expected_fee": None, "variance": None}

    if case.method == FeeMethod.FIXED_AMOUNT:
        if case.fixed_fee_amount is None:
            return {"state": FindingState.UNKNOWN, "expected_fee": None, "variance": None}
        expected = money(case.fixed_fee_amount)
    elif case.method == FeeMethod.PERCENT_OF_SUPPORTED_COST:
        if case.supported_cost is None or case.fee_rate is None:
            return {"state": FindingState.UNKNOWN, "expected_fee": None, "variance": None}
        expected = money(case.supported_cost * case.fee_rate)
    else:
        return {"state": FindingState.UNKNOWN, "expected_fee": None, "variance": None}

    if case.fee_ceiling is not None:
        expected = min(expected, money(case.fee_ceiling))
    billed = money(case.billed_fee)
    variance = money(expected - billed)
    state = (
        FindingState.RECOVERY_CANDIDATE if variance > 0
        else FindingState.PAYABLE_CANDIDATE if variance < 0
        else FindingState.NO_VARIANCE
    )
    return {"state": state, "expected_fee": expected, "variance": variance}
