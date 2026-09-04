from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Sequence

from aviation_recovery import Status
from claim_workflow import (
    ClaimAuditEvent,
    ClaimLifecycle,
    ClaimRecord,
    SettlementEvidence,
    SettlementType,
    WorkflowError,
    transition_claim,
)


CASE_SCHEMA_VERSION = 1


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("workflow timestamps must be timezone-aware")
    return parsed


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def serialize_record(record: ClaimRecord) -> dict[str, Any]:
    return {
        "claim_id": record.claim_id,
        "lifecycle": record.lifecycle.value,
        "currency": record.currency,
        "asserted_recovery_amount": str(record.asserted_recovery_amount),
        "verified_settled_amount": str(record.verified_settled_amount),
    }


def serialize_event(event: ClaimAuditEvent) -> dict[str, Any]:
    return {
        "claim_id": event.claim_id,
        "from_state": event.from_state.value,
        "to_state": event.to_state.value,
        "occurred_at": event.occurred_at.isoformat(),
        "actor": event.actor,
        "reason": event.reason,
        "settlement_reference": event.settlement_reference,
    }


def parse_record(raw: Mapping[str, Any]) -> ClaimRecord:
    return ClaimRecord(
        claim_id=str(raw["claim_id"]).strip(),
        lifecycle=ClaimLifecycle(str(raw["lifecycle"])),
        currency=str(raw["currency"]).strip().upper(),
        asserted_recovery_amount=_decimal(raw.get("asserted_recovery_amount", "0")),
        verified_settled_amount=_decimal(raw.get("verified_settled_amount", "0")),
    )


def parse_event(raw: Mapping[str, Any]) -> ClaimAuditEvent:
    return ClaimAuditEvent(
        claim_id=str(raw["claim_id"]).strip(),
        from_state=ClaimLifecycle(str(raw["from_state"])),
        to_state=ClaimLifecycle(str(raw["to_state"])),
        occurred_at=_dt(str(raw["occurred_at"])),
        actor=str(raw["actor"]).strip(),
        reason=str(raw["reason"]).strip(),
        settlement_reference=(
            str(raw["settlement_reference"]).strip()
            if raw.get("settlement_reference") is not None
            else None
        ),
    )


def parse_bundle(raw: Mapping[str, Any] | None) -> tuple[list[ClaimRecord], list[ClaimAuditEvent]]:
    if raw is None:
        return [], []
    version = int(raw.get("schema_version", CASE_SCHEMA_VERSION))
    if version != CASE_SCHEMA_VERSION:
        raise ValueError(f"unsupported workflow schema_version: {version}")
    records = [parse_record(item) for item in raw.get("records", [])]
    events = [parse_event(item) for item in raw.get("events", [])]
    validate_bundle(records, events)
    return records, events


def serialize_bundle(
    records: Sequence[ClaimRecord], events: Sequence[ClaimAuditEvent]
) -> dict[str, Any]:
    validate_bundle(records, events)
    return {
        "schema_version": CASE_SCHEMA_VERSION,
        "records": [serialize_record(record) for record in records],
        "events": [serialize_event(event) for event in events],
    }


def validate_bundle(
    records: Sequence[ClaimRecord], events: Sequence[ClaimAuditEvent]
) -> None:
    record_ids = [record.claim_id for record in records]
    if any(not claim_id for claim_id in record_ids):
        raise ValueError("workflow record claim_id is required")
    if len(set(record_ids)) != len(record_ids):
        raise ValueError("duplicate workflow record claim_id")

    record_map = {record.claim_id: record for record in records}
    events_by_claim: dict[str, list[ClaimAuditEvent]] = {}
    for event in events:
        if event.claim_id not in record_map:
            raise ValueError("workflow event references unknown claim_id")
        if not event.actor or not event.reason:
            raise ValueError("workflow event actor and reason are required")
        events_by_claim.setdefault(event.claim_id, []).append(event)

    for claim_id, claim_events in events_by_claim.items():
        previous_to: ClaimLifecycle | None = None
        previous_time: datetime | None = None
        for event in claim_events:
            if previous_to is not None and event.from_state != previous_to:
                raise ValueError(f"non-contiguous workflow audit trail for {claim_id}")
            if previous_time is not None and event.occurred_at < previous_time:
                raise ValueError(f"non-monotonic workflow audit timestamps for {claim_id}")
            previous_to = event.to_state
            previous_time = event.occurred_at
        if claim_events and record_map[claim_id].lifecycle != claim_events[-1].to_state:
            raise ValueError(f"workflow record state does not match audit trail for {claim_id}")


def _evaluation_index(evaluated: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(item.get("claim_id")): item
        for item in evaluated.get("results", [])
        if item.get("claim_id") is not None
    }


def _dossier_index(evaluated: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(item.get("claim", {}).get("claim_id")): item
        for item in evaluated.get("dossiers", [])
        if item.get("claim", {}).get("claim_id") is not None
    }


def reconcile_bundle_with_evaluation(
    records: Sequence[ClaimRecord], evaluated: Mapping[str, Any]
) -> None:
    index = _evaluation_index(evaluated)
    for record in records:
        result = index.get(record.claim_id)
        if result is None:
            raise ValueError(f"workflow record references claim outside current cohort: {record.claim_id}")
        currency = str(result.get("currency", "")).upper()
        if record.currency != currency:
            raise ValueError(f"workflow currency differs from current evaluation for {record.claim_id}")
        amount = _decimal(result.get("net_recoverable", "0"))
        if record.asserted_recovery_amount != amount:
            raise ValueError(f"workflow asserted amount differs from current evaluation for {record.claim_id}")


def initialize_record(
    evaluated: Mapping[str, Any], claim_id: str
) -> ClaimRecord:
    normalized = str(claim_id).strip()
    result = _evaluation_index(evaluated).get(normalized)
    if result is None:
        raise ValueError("claim_id not found in current cohort")
    status = str(result.get("status", ""))
    if status not in {Status.CLAIM_READY.value, Status.REVIEW_REQUIRED.value, Status.BLOCKED.value}:
        raise ValueError(f"workflow cannot start for status {status or 'unknown'}")
    return ClaimRecord(
        claim_id=normalized,
        lifecycle=ClaimLifecycle.DETECTED,
        currency=str(result.get("currency", "")).upper(),
        asserted_recovery_amount=_decimal(result.get("net_recoverable", "0")),
    )


def transition_bundle(
    *,
    evaluated: Mapping[str, Any],
    bundle: Mapping[str, Any] | None,
    claim_id: str,
    target: str,
    occurred_at: str,
    actor: str,
    reason: str,
    settlement: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    records, events = parse_bundle(bundle)
    reconcile_bundle_with_evaluation(records, evaluated)

    normalized = str(claim_id).strip()
    target_state = ClaimLifecycle(str(target))
    record_map = {record.claim_id: record for record in records}
    record = record_map.get(normalized)
    if record is None:
        record = initialize_record(evaluated, normalized)
        records.append(record)

    result = _evaluation_index(evaluated)[normalized]
    dossier = _dossier_index(evaluated).get(normalized, {})
    evaluation_status = Status(str(result.get("status")))
    externalization_gate_passed = (
        evaluation_status == Status.CLAIM_READY
        and not result.get("blocking_issues")
        and not dossier.get("lineage_gaps")
    )

    event_time = _dt(occurred_at)
    claim_events = [event for event in events if event.claim_id == normalized]
    if claim_events and event_time < claim_events[-1].occurred_at:
        raise ValueError("workflow transition timestamp precedes prior audit event")

    settlement_evidence = None
    if settlement is not None:
        settlement_evidence = SettlementEvidence(
            settlement_type=SettlementType(str(settlement["settlement_type"])),
            amount=_decimal(settlement["amount"]),
            currency=str(settlement["currency"]).strip().upper(),
            reference=str(settlement["reference"]).strip(),
        )

    updated, event = transition_claim(
        record,
        target_state,
        occurred_at=event_time,
        actor=str(actor).strip(),
        reason=str(reason).strip(),
        evaluation_status=evaluation_status,
        externalization_gate_passed=externalization_gate_passed,
        settlement_evidence=settlement_evidence,
    )

    if updated.verified_settled_amount > updated.asserted_recovery_amount:
        raise WorkflowError(
            "settlement amount exceeds the currently asserted recovery amount; revise and re-review the claim before recording settlement"
        )

    records = [updated if item.claim_id == normalized else item for item in records]
    events.append(event)
    return serialize_bundle(records, events)


def build_case_export(
    *,
    cohort: Mapping[str, Any],
    evaluated: Mapping[str, Any],
    workflow_bundle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    records, events = parse_bundle(workflow_bundle)
    reconcile_bundle_with_evaluation(records, evaluated)
    return {
        "schema_version": CASE_SCHEMA_VERSION,
        "kind": "aervind_assisted_case",
        "cohort": dict(cohort),
        "workflow": serialize_bundle(records, events),
    }
