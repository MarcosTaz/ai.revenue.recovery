from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Iterable, Tuple

from .domain import AuditEvent


GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class ChainedAuditEvent:
    event: AuditEvent
    previous_hash: str
    event_hash: str


def _canonical_event_payload(event: AuditEvent) -> str:
    payload = asdict(event)
    occurred_at = payload.get("occurred_at")
    if isinstance(occurred_at, datetime):
        payload["occurred_at"] = occurred_at.isoformat()
    payload["evidence_ids"] = list(event.evidence_ids)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_event_hash(event: AuditEvent, previous_hash: str) -> str:
    if len(previous_hash) != 64:
        raise ValueError("previous_hash must be a 64-character SHA-256 digest")
    int(previous_hash, 16)
    payload = f"{previous_hash}:{_canonical_event_payload(event)}".encode("utf-8")
    return sha256(payload).hexdigest()


def append_event(chain: Tuple[ChainedAuditEvent, ...], event: AuditEvent) -> Tuple[ChainedAuditEvent, ...]:
    if any(item.event.event_id == event.event_id for item in chain):
        raise ValueError("duplicate audit event id")
    previous_hash = chain[-1].event_hash if chain else GENESIS_HASH
    chained = ChainedAuditEvent(
        event=event,
        previous_hash=previous_hash,
        event_hash=compute_event_hash(event, previous_hash),
    )
    return (*chain, chained)


def verify_chain(chain: Iterable[ChainedAuditEvent]) -> bool:
    previous_hash = GENESIS_HASH
    seen_ids: set[str] = set()
    for item in chain:
        if item.event.event_id in seen_ids:
            return False
        seen_ids.add(item.event.event_id)
        if item.previous_hash != previous_hash:
            return False
        expected = compute_event_hash(item.event, previous_hash)
        if item.event_hash != expected:
            return False
        previous_hash = item.event_hash
    return True
