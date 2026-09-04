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


@dataclass(frozen=True)
class FinalPaymentInput:
    contract_id: str
    approved_completion_voucher_amount: Optional[Decimal]
    verified_cumulative_payments: Optional[Decimal]
    verified_refunds_credits_offsets: Optional[Decimal]
    completion_voucher_approved: bool
    contract_terms_complied: bool
    allowable_cost_support_complete: bool
    fee_terms_supported: bool
    release_state: ReleaseState
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


def reconcile_final_payment(case: FinalPaymentInput):
    """Reconcile an approved completion voucher against verified payments.

    This represents the economic check anchored to FAR 52.216-7(h), not a claim
    viability determination. Refunds, rebates, credits and other verified offsets
    are kept symmetric and reduce any apparent contractor-side balance.
    """
    if not case.evidence_supported:
        return {
            "state": FindingState.UNKNOWN,
            "variance": None,
            "expected_net_payment": None,
            "explanation": "Final-payment evidence is incomplete.",
        }
    if not case.completion_voucher_approved:
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "variance": None,
            "expected_net_payment": None,
            "explanation": "A draft or unapproved completion voucher cannot establish the final-payment reconciliation baseline.",
        }
    if not case.contract_terms_complied or not case.allowable_cost_support_complete or not case.fee_terms_supported:
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "variance": None,
            "expected_net_payment": None,
            "explanation": "Contract compliance, allowable-cost support and fee terms must be supported before final-payment reconciliation.",
        }
    if case.approved_completion_voucher_amount is None or case.verified_cumulative_payments is None:
        return {
            "state": FindingState.UNKNOWN,
            "variance": None,
            "expected_net_payment": None,
            "explanation": "Approved voucher amount and verified cumulative payments are required.",
        }
    offsets = case.verified_refunds_credits_offsets
    if offsets is None:
        return {
            "state": FindingState.UNKNOWN,
            "variance": None,
            "expected_net_payment": None,
            "explanation": "Refund, rebate, credit and offset status must be evidenced, including an evidenced zero.",
        }
    numeric = (
        case.approved_completion_voucher_amount,
        case.verified_cumulative_payments,
        offsets,
    )
    if any((not value.is_finite()) or value < 0 for value in numeric):
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "variance": None,
            "expected_net_payment": None,
            "explanation": "Negative or non-finite final-payment inputs require explicit accounting review.",
        }

    expected_net = money(case.approved_completion_voucher_amount - offsets)
    if expected_net < 0:
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "variance": None,
            "expected_net_payment": expected_net,
            "explanation": "Verified offsets exceed the approved voucher amount; qualified review is required before classifying the balance.",
        }
    variance = money(expected_net - case.verified_cumulative_payments)

    if variance == 0:
        return {
            "state": FindingState.NO_VARIANCE,
            "variance": variance,
            "expected_net_payment": expected_net,
            "explanation": "Verified cumulative payments match the approved completion-voucher economics after evidenced offsets.",
        }

    if case.release_state in {ReleaseState.SIGNED_GENERAL, ReleaseState.SIGNED_WITH_RESERVATION, ReleaseState.UNKNOWN}:
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "variance": variance,
            "expected_net_payment": expected_net,
            "explanation": "A release or unknown release state can affect further action; legal review is required before treating the variance as collectible or payable.",
        }

    state = FindingState.RECOVERY_CANDIDATE if variance > 0 else FindingState.PAYABLE_CANDIDATE
    explanation = (
        "Verified cumulative payments are below approved completion-voucher economics after evidenced offsets."
        if variance > 0
        else "Verified cumulative payments exceed approved completion-voucher economics after evidenced offsets."
    )
    return {
        "state": state,
        "variance": variance,
        "expected_net_payment": expected_net,
        "explanation": explanation,
    }
