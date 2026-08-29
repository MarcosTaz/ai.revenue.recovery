from __future__ import annotations

from datetime import datetime
from typing import Sequence, Tuple

from .audit import ChainedAuditEvent, append_event, verify_chain
from .domain import AuditEvent
from .operation import AuditOperationResult
from .review import HumanReview


def build_operation_audit_trace(
    result: AuditOperationResult,
    organization_id: str,
    actor_user_id: str,
    occurred_at: datetime,
    audit_run_id: str,
    reviews: Sequence[HumanReview] = (),
) -> Tuple[ChainedAuditEvent, ...]:
    if occurred_at.tzinfo is None:
        raise ValueError("audit trace timestamp must be timezone-aware")
    if not audit_run_id.strip():
        raise ValueError("audit_run_id is required")
    if not organization_id.strip() or not actor_user_id.strip():
        raise ValueError("organization_id and actor_user_id are required")

    evidence_ids = tuple(item.evidence_id for item in result.evidence)
    chain: Tuple[ChainedAuditEvent, ...] = ()
    chain = append_event(
        chain,
        AuditEvent(
            event_id=f"{audit_run_id}:run",
            occurred_at=occurred_at,
            actor=actor_user_id,
            action="RUN_NORMALIZED_AUDIT",
            subject_id=result.finding.finding_id,
            evidence_ids=evidence_ids,
        ),
    )
    for index, review in enumerate(reviews):
        chain = append_event(
            chain,
            AuditEvent(
                event_id=f"{audit_run_id}:review:{index}",
                occurred_at=review.reviewed_at,
                actor=review.reviewer_id,
                action=f"REVIEW:{review.decision.value}",
                subject_id=review.finding_id,
                evidence_ids=evidence_ids,
            ),
        )
    chain = append_event(
        chain,
        AuditEvent(
            event_id=f"{audit_run_id}:output",
            occurred_at=occurred_at,
            actor=actor_user_id,
            action="BUILD_REVIEW_OUTPUT",
            subject_id=organization_id,
            evidence_ids=evidence_ids,
        ),
    )
    if not verify_chain(chain):
        raise RuntimeError("audit trace failed integrity verification")
    return chain
