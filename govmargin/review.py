from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"


@dataclass(frozen=True)
class HumanReview:
    finding_id: str
    reviewer_id: str
    reviewer_role: str
    decision: ReviewDecision
    rationale: str
    reviewed_at: datetime

    def __post_init__(self):
        if not self.reviewer_id.strip():
            raise ValueError("Reviewer identity is required")
        if not self.reviewer_role.strip():
            raise ValueError("Reviewer role is required")
        if not self.rationale.strip():
            raise ValueError("Review rationale is required")
        if self.reviewed_at.tzinfo is None:
            raise ValueError("Review timestamp must be timezone-aware")


def review_now(finding_id: str, reviewer_id: str, reviewer_role: str, decision: ReviewDecision, rationale: str) -> HumanReview:
    return HumanReview(finding_id, reviewer_id, reviewer_role, decision, rationale, datetime.now(timezone.utc))
