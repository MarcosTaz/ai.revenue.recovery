from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Literal

WorkflowState = Literal[
    "DETECTED","ANALYSIS","EVIDENCE_COLLECTION","REVIEW","CLAIM_READY","SUBMITTED",
    "DISPUTED","NEGOTIATION","SETTLED","PAYMENT_PENDING","PAID","REJECTED",
]

_ALLOWED: dict[str, set[str]] = {
    "DETECTED":{"ANALYSIS","REJECTED"},
    "ANALYSIS":{"EVIDENCE_COLLECTION","REVIEW","REJECTED"},
    "EVIDENCE_COLLECTION":{"REVIEW","REJECTED"},
    "REVIEW":{"CLAIM_READY","EVIDENCE_COLLECTION","REJECTED"},
    "CLAIM_READY":{"SUBMITTED","REJECTED"},
    "SUBMITTED":{"DISPUTED","NEGOTIATION","SETTLED","REJECTED"},
    "DISPUTED":{"NEGOTIATION","SETTLED","REJECTED"},
    "NEGOTIATION":{"SETTLED","REJECTED"},
    "SETTLED":{"PAYMENT_PENDING"},
    "PAYMENT_PENDING":{"PAID"},
    "PAID":set(),"REJECTED":set(),
}

@dataclass(frozen=True, slots=True)
class PaymentRecord:
    payment_id: str
    amount: Decimal
    currency: str
    payment_evidence_ref: str

@dataclass(frozen=True, slots=True)
class ClaimCase:
    case_id: str
    workspace_id: str
    claim_amount: Decimal
    currency: str
    state: WorkflowState = "DETECTED"
    settled_amount: Decimal = Decimal("0")
    settlement_evidence_ref: str | None = None
    payments: tuple[PaymentRecord, ...] = ()

    @property
    def paid_amount(self) -> Decimal:
        return sum((p.amount for p in self.payments), Decimal("0"))


def advance_case(case: ClaimCase, new_state: WorkflowState, *, settled_amount: Decimal | None = None, settlement_evidence_ref: str | None = None) -> ClaimCase:
    if new_state not in _ALLOWED[case.state]:
        raise ValueError(f"INVALID_CLAIM_TRANSITION:{case.state}->{new_state}")
    if new_state == "SETTLED":
        if settled_amount is None or settled_amount <= 0:
            raise ValueError("SETTLEMENT_REQUIRES_POSITIVE_AMOUNT")
        if settled_amount > case.claim_amount:
            raise ValueError("SETTLEMENT_EXCEEDS_CLAIM")
        if not settlement_evidence_ref:
            raise ValueError("SETTLEMENT_REQUIRES_EVIDENCE")
        return replace(case,state="SETTLED",settled_amount=settled_amount,settlement_evidence_ref=settlement_evidence_ref)
    if settled_amount is not None or settlement_evidence_ref is not None:
        raise ValueError("SETTLEMENT_FIELDS_ONLY_ALLOWED_AT_SETTLED")
    if new_state == "PAID":
        if case.paid_amount != case.settled_amount or case.settled_amount <= 0:
            raise ValueError("PAID_REQUIRES_FULL_VERIFIED_SETTLEMENT_PAYMENT")
    return replace(case,state=new_state)


def record_payment(case: ClaimCase, payment: PaymentRecord) -> ClaimCase:
    if case.state not in {"SETTLED","PAYMENT_PENDING"}:
        raise ValueError("PAYMENT_REQUIRES_SETTLED_CASE")
    if payment.amount <= 0:
        raise ValueError("PAYMENT_REQUIRES_POSITIVE_AMOUNT")
    if payment.currency != case.currency:
        raise ValueError("PAYMENT_CURRENCY_MISMATCH")
    if not payment.payment_evidence_ref:
        raise ValueError("PAYMENT_REQUIRES_EVIDENCE")
    if any(p.payment_id == payment.payment_id for p in case.payments):
        raise ValueError("DUPLICATE_PAYMENT_ID")
    if case.paid_amount + payment.amount > case.settled_amount:
        raise ValueError("PAYMENTS_EXCEED_SETTLEMENT")
    updated = replace(case,payments=case.payments + (payment,))
    return replace(updated,state="PAYMENT_PENDING")
