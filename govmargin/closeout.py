from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from .engine import FindingState, money


class ReleaseState(str, Enum):
    NOT_SIGNED = "NOT_SIGNED"
    SIGNED_WITH_RESERVATION = "SIGNED_WITH_RESERVATION"
    SIGNED_GENERAL = "SIGNED_GENERAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FinalVoucherInput:
    contract_id: str
    supported_final_economics: Decimal
    completion_voucher_amount: Decimal
    final_rates_settled: bool
    contract_physically_complete: bool
    release_state: ReleaseState
    voucher_date: Optional[date]
    evidence_supported: bool


def reconcile_final_voucher(case: FinalVoucherInput):
    if not case.evidence_supported:
        return {"state": FindingState.UNKNOWN, "variance": None, "explanation": "Closeout evidence is incomplete."}
    if not case.final_rates_settled or not case.contract_physically_complete:
        return {"state": FindingState.REQUIRES_REVIEW, "variance": None, "explanation": "Final-voucher prerequisites are not satisfied."}
    variance = money(case.supported_final_economics - case.completion_voucher_amount)
    if variance == 0:
        return {"state": FindingState.NO_VARIANCE, "variance": variance, "explanation": "Completion voucher matches supported final economics."}
    if case.release_state in {ReleaseState.SIGNED_GENERAL, ReleaseState.SIGNED_WITH_RESERVATION, ReleaseState.UNKNOWN}:
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "variance": variance,
            "explanation": "A release state can affect recoverability; legal review is required before asserting entitlement.",
        }
    state = FindingState.RECOVERY_CANDIDATE if variance > 0 else FindingState.PAYABLE_CANDIDATE
    return {"state": state, "variance": variance, "explanation": "Final-voucher variance exists before any release blocker is identified."}
