from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum

from aviation_recovery import Status


_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class ClaimLifecycle(str, Enum):
    DETECTED = "detected"
    REVIEWING = "reviewing"
    CLAIM_READY = "claim_ready"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    DISPUTED = "disputed"
    APPROVED = "approved"
    REJECTED = "rejected"
    SETTLED = "settled"


class SettlementType(str, Enum):
    CASH_RECEIPT = "cash_receipt"
    CREDIT_MEMO = "credit_memo"
    CONTRACTUAL_OFFSET = "contractual_offset"
    REFUND = "refund"


@dataclass(frozen=True)
class SettlementEvidence:
    settlement_type: SettlementType
    amount: Decimal
    currency: str
    reference: str


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    lifecycle: ClaimLifecycle
    currency: str
    asserted_recovery_amount: Decimal
    verified_settled_amount: Decimal = Decimal("0")


@dataclass(frozen=True)
class ClaimAuditEvent:
    claim_id: str
    from_state: ClaimLifecycle
    to_state: ClaimLifecycle
    occurred_at: datetime
    actor: str
    reason: str
    external_reference: str | None = None
    settlement_reference: str | None = None


class WorkflowError(ValueError):
    pass


_ALLOWED_TRANSITIONS: dict[ClaimLifecycle, set[ClaimLifecycle]] = {
    ClaimLifecycle.DETECTED: {ClaimLifecycle.REVIEWING},
    ClaimLifecycle.REVIEWING: {ClaimLifecycle.CLAIM_READY, ClaimLifecycle.REJECTED},
    ClaimLifecycle.CLAIM_READY: {ClaimLifecycle.SUBMITTED, ClaimLifecycle.REVIEWING},
    ClaimLifecycle.SUBMITTED: {
        ClaimLifecycle.ACKNOWLEDGED,
        ClaimLifecycle.DISPUTED,
        ClaimLifecycle.APPROVED,
        ClaimLifecycle.REJECTED,
    },
    ClaimLifecycle.ACKNOWLEDGED: {
        ClaimLifecycle.DISPUTED,
        ClaimLifecycle.APPROVED,
        ClaimLifecycle.REJECTED,
    },
    ClaimLifecycle.DISPUTED: {
        ClaimLifecycle.APPROVED,
        ClaimLifecycle.REJECTED,
        ClaimLifecycle.REVIEWING,
    },
    ClaimLifecycle.APPROVED: {ClaimLifecycle.SETTLED},
    ClaimLifecycle.REJECTED: {ClaimLifecycle.REVIEWING},
    ClaimLifecycle.SETTLED: set(),
}

_EXTERNAL_SOURCE_STATES = {
    ClaimLifecycle.SUBMITTED,
    ClaimLifecycle.ACKNOWLEDGED,
    ClaimLifecycle.DISPUTED,
}


def allowed_transitions(state: ClaimLifecycle) -> tuple[ClaimLifecycle, ...]:
    return tuple(sorted(_ALLOWED_TRANSITIONS[state], key=lambda value: value.value))


def external_reference_required(
    current: ClaimLifecycle, target: ClaimLifecycle
) -> bool:
    if target == ClaimLifecycle.SUBMITTED:
        return True
    if current in _EXTERNAL_SOURCE_STATES and target in {
        ClaimLifecycle.ACKNOWLEDGED,
        ClaimLifecycle.DISPUTED,
        ClaimLifecycle.APPROVED,
        ClaimLifecycle.REJECTED,
    }:
        return True
    return False


def _validate_amount(value: Decimal, name: str) -> None:
    if not value.is_finite():
        raise WorkflowError(f"{name} must be finite")
    if value < 0:
        raise WorkflowError(f"{name} cannot be negative")


def _validate_currency(value: str, name: str = "currency") -> None:
    if not _CURRENCY_RE.fullmatch(value.strip().upper()):
        raise WorkflowError(f"{name} must be a three-letter code")


def _validate_record(record: ClaimRecord) -> None:
    if not record.claim_id.strip():
        raise WorkflowError("claim_id is required")
    _validate_currency(record.currency)
    _validate_amount(record.asserted_recovery_amount, "asserted_recovery_amount")
    _validate_amount(record.verified_settled_amount, "verified_settled_amount")
    if record.lifecycle != ClaimLifecycle.SETTLED and record.verified_settled_amount != 0:
        raise WorkflowError("unsettled workflow record cannot contain verified settled value")
    if record.lifecycle == ClaimLifecycle.SETTLED:
        if record.verified_settled_amount <= 0:
            raise WorkflowError("settled workflow record requires positive verified settled value")
        if record.verified_settled_amount > record.asserted_recovery_amount:
            raise WorkflowError("verified settled value cannot exceed asserted recovery amount")


def transition_claim(
    record: ClaimRecord,
    target: ClaimLifecycle,
    *,
    occurred_at: datetime,
    actor: str,
    reason: str,
    evaluation_status: Status | None = None,
    externalization_gate_passed: bool = False,
    external_reference: str | None = None,
    settlement_evidence: SettlementEvidence | None = None,
) -> tuple[ClaimRecord, ClaimAuditEvent]:
    _validate_record(record)

    if not actor.strip():
        raise WorkflowError("actor is required")
    if not reason.strip():
        raise WorkflowError("reason is required")
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise WorkflowError("occurred_at must be timezone-aware")

    allowed = _ALLOWED_TRANSITIONS[record.lifecycle]
    if target not in allowed:
        raise WorkflowError(
            f"invalid transition: {record.lifecycle.value} -> {target.value}"
        )

    normalized_external_reference = (
        str(external_reference).strip() if external_reference is not None else ""
    )
    if external_reference_required(record.lifecycle, target) and not normalized_external_reference:
        raise WorkflowError(
            f"{target.value} requires an external evidence/reference identifier"
        )

    if target == ClaimLifecycle.CLAIM_READY:
        if evaluation_status != Status.CLAIM_READY:
            raise WorkflowError("claim_ready requires a claim-ready economic evaluation")
        if not externalization_gate_passed:
            raise WorkflowError("claim_ready requires the evidence-lineage gate to pass")

    settled_amount = record.verified_settled_amount
    settlement_reference: str | None = None

    if target == ClaimLifecycle.SETTLED:
        if settlement_evidence is None:
            raise WorkflowError("settled requires economic settlement evidence")
        _validate_amount(settlement_evidence.amount, "settlement amount")
        if settlement_evidence.amount <= 0:
            raise WorkflowError("settlement amount must be positive")
        if settlement_evidence.amount > record.asserted_recovery_amount:
            raise WorkflowError(
                "settlement amount exceeds asserted recovery amount; revise and re-review the claim before settlement"
            )
        _validate_currency(settlement_evidence.currency, "settlement currency")
        if settlement_evidence.currency.strip().upper() != record.currency.strip().upper():
            raise WorkflowError("settlement currency mismatch")
        if not settlement_evidence.reference.strip():
            raise WorkflowError("settlement evidence reference is required")
        settled_amount = settlement_evidence.amount
        settlement_reference = settlement_evidence.reference.strip()
    elif settlement_evidence is not None:
        raise WorkflowError("settlement evidence is accepted only for a settled transition")

    updated = replace(
        record,
        lifecycle=target,
        verified_settled_amount=settled_amount,
    )
    event = ClaimAuditEvent(
        claim_id=record.claim_id,
        from_state=record.lifecycle,
        to_state=target,
        occurred_at=occurred_at,
        actor=actor.strip(),
        reason=reason.strip(),
        external_reference=normalized_external_reference or None,
        settlement_reference=settlement_reference,
    )
    _validate_record(updated)
    return updated, event
