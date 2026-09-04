from __future__ import annotations

import hashlib
import json
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
    allowed_transitions,
    external_reference_required,
    transition_claim,
)


CASE_SCHEMA_VERSION = 2
_RELEASED_STATES = {
    ClaimLifecycle.CLAIM_READY,
    ClaimLifecycle.SUBMITTED,
    ClaimLifecycle.ACKNOWLEDGED,
    ClaimLifecycle.DISPUTED,
    ClaimLifecycle.APPROVED,
    ClaimLifecycle.SETTLED,
}


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("workflow timestamps must be timezone-aware")
    return parsed


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def cohort_digest(cohort: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        cohort,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


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
        "external_reference": event.external_reference,
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
        external_reference=(
            str(raw["external_reference"]).strip()
            if raw.get("external_reference") is not None
            else None
        ),
        settlement_reference=(
            str(raw["settlement_reference"]).strip()
            if raw.get("settlement_reference") is not None
            else None
        ),
    )


def parse_artifact(raw: Mapping[str, Any]) -> dict[str, Any]:
    artifact = {
        "claim_id": str(raw["claim_id"]).strip(),
        "kind": str(raw["kind"]).strip(),
        "generated_at": _dt(str(raw["generated_at"])).isoformat(),
        "generated_by": str(raw["generated_by"]).strip(),
        "content_sha256": str(raw["content_sha256"]).strip().lower(),
        "submission_status": str(raw.get("submission_status", "not_submitted")).strip(),
    }
    if not artifact["claim_id"] or not artifact["kind"] or not artifact["generated_by"]:
        raise ValueError("workflow artifact claim_id, kind and generated_by are required")
    digest = artifact["content_sha256"]
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("workflow artifact content_sha256 is invalid")
    if artifact["submission_status"] != "not_submitted":
        raise ValueError("generated artifacts cannot imply external submission")
    return artifact


def parse_bundle(
    raw: Mapping[str, Any] | None,
) -> tuple[list[ClaimRecord], list[ClaimAuditEvent], list[dict[str, Any]], str | None]:
    if raw is None:
        return [], [], [], None
    version = int(raw.get("schema_version", CASE_SCHEMA_VERSION))
    if version != CASE_SCHEMA_VERSION:
        raise ValueError(f"unsupported workflow schema_version: {version}")
    records = [parse_record(item) for item in raw.get("records", [])]
    events = [parse_event(item) for item in raw.get("events", [])]
    artifacts = [parse_artifact(item) for item in raw.get("artifacts", [])]
    digest = str(raw.get("cohort_digest", "")).strip().lower() or None
    if digest is not None and (
        len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest)
    ):
        raise ValueError("workflow cohort_digest is invalid")
    validate_bundle(records, events, artifacts)
    return records, events, artifacts, digest


def serialize_bundle(
    records: Sequence[ClaimRecord],
    events: Sequence[ClaimAuditEvent],
    artifacts: Sequence[Mapping[str, Any]] = (),
    *,
    bound_cohort_digest: str | None = None,
) -> dict[str, Any]:
    normalized_artifacts = [parse_artifact(item) for item in artifacts]
    validate_bundle(records, events, normalized_artifacts)
    payload: dict[str, Any] = {
        "schema_version": CASE_SCHEMA_VERSION,
        "records": [serialize_record(record) for record in records],
        "events": [serialize_event(event) for event in events],
        "artifacts": normalized_artifacts,
    }
    if bound_cohort_digest:
        payload["cohort_digest"] = bound_cohort_digest
    return payload


def _state_at_time(
    claim_events: Sequence[ClaimAuditEvent], when: datetime
) -> ClaimLifecycle:
    state = ClaimLifecycle.DETECTED
    for event in claim_events:
        if event.occurred_at > when:
            break
        state = event.to_state
    return state


def validate_bundle(
    records: Sequence[ClaimRecord],
    events: Sequence[ClaimAuditEvent],
    artifacts: Sequence[Mapping[str, Any]] = (),
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
        if event.to_state not in allowed_transitions(event.from_state):
            raise ValueError(
                f"invalid workflow audit transition: {event.from_state.value} -> {event.to_state.value}"
            )
        if (
            external_reference_required(event.from_state, event.to_state)
            and not event.external_reference
        ):
            raise ValueError(
                f"workflow audit event {event.to_state.value} requires external reference"
            )
        if event.to_state == ClaimLifecycle.SETTLED and not event.settlement_reference:
            raise ValueError("settled audit event requires settlement reference")
        if event.to_state != ClaimLifecycle.SETTLED and event.settlement_reference:
            raise ValueError("settlement reference is valid only on settled audit event")
        events_by_claim.setdefault(event.claim_id, []).append(event)

    for claim_id, record in record_map.items():
        if record.asserted_recovery_amount < 0 or record.verified_settled_amount < 0:
            raise ValueError("workflow record amounts cannot be negative")
        claim_events = events_by_claim.get(claim_id, [])
        if not claim_events:
            if record.lifecycle != ClaimLifecycle.DETECTED:
                raise ValueError(
                    f"workflow record without audit trail must remain detected: {claim_id}"
                )
            if record.verified_settled_amount != 0:
                raise ValueError("detected workflow record cannot contain settlement value")
            continue

        if claim_events[0].from_state != ClaimLifecycle.DETECTED:
            raise ValueError(f"workflow audit trail must begin at detected for {claim_id}")
        previous_to: ClaimLifecycle | None = None
        previous_time: datetime | None = None
        for event in claim_events:
            if previous_to is not None and event.from_state != previous_to:
                raise ValueError(f"non-contiguous workflow audit trail for {claim_id}")
            if previous_time is not None and event.occurred_at < previous_time:
                raise ValueError(f"non-monotonic workflow audit timestamps for {claim_id}")
            previous_to = event.to_state
            previous_time = event.occurred_at
        if record.lifecycle != claim_events[-1].to_state:
            raise ValueError(f"workflow record state does not match audit trail for {claim_id}")
        if record.lifecycle == ClaimLifecycle.SETTLED:
            if record.verified_settled_amount <= 0:
                raise ValueError("settled workflow record requires positive settled amount")
            if record.verified_settled_amount > record.asserted_recovery_amount:
                raise ValueError("verified settled amount exceeds asserted recovery amount")
        elif record.verified_settled_amount != 0:
            raise ValueError("unsettled workflow record cannot contain settlement value")

    for artifact in artifacts:
        claim_id = str(artifact.get("claim_id", ""))
        if claim_id not in record_map:
            raise ValueError("workflow artifact references unknown claim_id")
        if artifact.get("kind") != "claim_package":
            raise ValueError("unsupported workflow artifact kind")
        when = _dt(str(artifact["generated_at"]))
        if _state_at_time(events_by_claim.get(claim_id, []), when) != ClaimLifecycle.CLAIM_READY:
            raise ValueError("claim package artifact must be generated while lifecycle is claim_ready")


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
            raise ValueError(
                f"workflow record references claim outside current cohort: {record.claim_id}"
            )
        currency = str(result.get("currency", "")).upper()
        if record.currency != currency:
            raise ValueError(
                f"workflow currency differs from current evaluation for {record.claim_id}"
            )
        amount = _decimal(result.get("net_recoverable", "0"))
        if record.asserted_recovery_amount != amount:
            raise ValueError(
                f"workflow asserted amount differs from current evaluation for {record.claim_id}"
            )


def bind_or_validate_cohort_revision(
    *,
    cohort: Mapping[str, Any],
    records: Sequence[ClaimRecord],
    existing_digest: str | None,
) -> str:
    current = cohort_digest(cohort)
    if existing_digest is None:
        if any(record.lifecycle in _RELEASED_STATES for record in records):
            raise ValueError("released workflow is missing its bound cohort digest")
        return current
    if existing_digest == current:
        return current
    if any(record.lifecycle in _RELEASED_STATES for record in records):
        raise ValueError(
            "cohort changed after a claim reached a released lifecycle state; create a new reviewed case revision instead of rewriting the audit history"
        )
    return current


def initialize_record(evaluated: Mapping[str, Any], claim_id: str) -> ClaimRecord:
    normalized = str(claim_id).strip()
    result = _evaluation_index(evaluated).get(normalized)
    if result is None:
        raise ValueError("claim_id not found in current cohort")
    status = str(result.get("status", ""))
    if status not in {
        Status.CLAIM_READY.value,
        Status.REVIEW_REQUIRED.value,
        Status.BLOCKED.value,
    }:
        raise ValueError(f"workflow cannot start for status {status or 'unknown'}")
    return ClaimRecord(
        claim_id=normalized,
        lifecycle=ClaimLifecycle.DETECTED,
        currency=str(result.get("currency", "")).upper(),
        asserted_recovery_amount=_decimal(result.get("net_recoverable", "0")),
    )


def transition_bundle(
    *,
    cohort: Mapping[str, Any],
    evaluated: Mapping[str, Any],
    bundle: Mapping[str, Any] | None,
    claim_id: str,
    target: str,
    occurred_at: str,
    actor: str,
    reason: str,
    external_reference: str | None = None,
    settlement: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    records, events, artifacts, existing_digest = parse_bundle(bundle)
    reconcile_bundle_with_evaluation(records, evaluated)
    bound_digest = bind_or_validate_cohort_revision(
        cohort=cohort,
        records=records,
        existing_digest=existing_digest,
    )

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
        external_reference=external_reference,
        settlement_evidence=settlement_evidence,
    )

    records = [updated if item.claim_id == normalized else item for item in records]
    events.append(event)
    return serialize_bundle(
        records,
        events,
        artifacts,
        bound_cohort_digest=bound_digest,
    )


def record_claim_package_artifact(
    *,
    cohort: Mapping[str, Any],
    evaluated: Mapping[str, Any],
    bundle: Mapping[str, Any],
    claim_id: str,
    generated_at: str,
    generated_by: str,
    content: str,
) -> dict[str, Any]:
    records, events, artifacts, existing_digest = parse_bundle(bundle)
    reconcile_bundle_with_evaluation(records, evaluated)
    bound_digest = bind_or_validate_cohort_revision(
        cohort=cohort,
        records=records,
        existing_digest=existing_digest,
    )
    normalized = str(claim_id).strip()
    record = next((item for item in records if item.claim_id == normalized), None)
    if record is None or record.lifecycle != ClaimLifecycle.CLAIM_READY:
        raise ValueError("claim package artifact requires workflow lifecycle claim_ready")
    when = _dt(generated_at).isoformat()
    who = str(generated_by).strip()
    if not who:
        raise ValueError("generated_by is required")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    artifact = {
        "claim_id": normalized,
        "kind": "claim_package",
        "generated_at": when,
        "generated_by": who,
        "content_sha256": digest,
        "submission_status": "not_submitted",
    }
    artifacts.append(artifact)
    return serialize_bundle(
        records,
        events,
        artifacts,
        bound_cohort_digest=bound_digest,
    )


def workflow_view(bundle: Mapping[str, Any] | None) -> dict[str, Any]:
    records, events, artifacts, digest = parse_bundle(bundle)
    event_counts: dict[str, int] = {}
    latest_event: dict[str, str] = {}
    for event in events:
        event_counts[event.claim_id] = event_counts.get(event.claim_id, 0) + 1
        latest_event[event.claim_id] = event.occurred_at.isoformat()
    artifact_counts: dict[str, int] = {}
    for artifact in artifacts:
        claim_id = str(artifact["claim_id"])
        artifact_counts[claim_id] = artifact_counts.get(claim_id, 0) + 1
    return {
        "schema_version": CASE_SCHEMA_VERSION,
        "cohort_digest": digest,
        "records": [
            {
                **serialize_record(record),
                "allowed_transitions": [
                    state.value for state in allowed_transitions(record.lifecycle)
                ],
                "audit_event_count": event_counts.get(record.claim_id, 0),
                "latest_event_at": latest_event.get(record.claim_id),
                "artifact_count": artifact_counts.get(record.claim_id, 0),
            }
            for record in records
        ],
        "events": [serialize_event(event) for event in events],
        "artifacts": list(artifacts),
    }


def build_case_export(
    *,
    cohort: Mapping[str, Any],
    evaluated: Mapping[str, Any],
    workflow_bundle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    records, events, artifacts, existing_digest = parse_bundle(workflow_bundle)
    reconcile_bundle_with_evaluation(records, evaluated)
    bound_digest = bind_or_validate_cohort_revision(
        cohort=cohort,
        records=records,
        existing_digest=existing_digest,
    )
    return {
        "schema_version": CASE_SCHEMA_VERSION,
        "kind": "aervind_assisted_case",
        "cohort": dict(cohort),
        "workflow": serialize_bundle(
            records,
            events,
            artifacts,
            bound_cohort_digest=bound_digest,
        ),
    }
