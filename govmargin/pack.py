from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List

from .domain import EconomicFinding
from .engine import FindingState
from .review import HumanReview, ReviewDecision


class PackStatus(str, Enum):
    DRAFT = "DRAFT"
    READY_FOR_CLIENT_FINANCE_REVIEW = "READY_FOR_CLIENT_FINANCE_REVIEW"
    NO_RECOVERY_PACK = "NO_RECOVERY_PACK"


@dataclass(frozen=True)
class RecoveryPack:
    organization_id: str
    status: PackStatus
    approved_recovery_candidates: List[dict]
    payable_exposures: List[dict]
    unresolved: List[dict]
    review_log: List[dict]


def _jsonable_finding(finding: EconomicFinding) -> dict:
    return {
        "finding_id": finding.finding_id,
        "contract_id": finding.contract_id,
        "state": finding.state.value,
        "expected_amount": None if finding.expected_amount is None else str(finding.expected_amount),
        "billed_amount": None if finding.billed_amount is None else str(finding.billed_amount),
        "paid_amount": None if finding.paid_amount is None else str(finding.paid_amount),
        "variance": None if finding.variance is None else str(finding.variance),
        "evidence_ids": list(finding.evidence_ids),
        "rule_ids": list(finding.rule_ids),
        "assumptions": list(finding.assumptions),
    }


def build_recovery_pack(
    organization_id: str,
    findings: Iterable[EconomicFinding],
    reviews: Iterable[HumanReview],
    required_approvals: int = 1,
) -> RecoveryPack:
    if required_approvals < 1:
        raise ValueError("required_approvals must be at least 1")
    findings = list(findings)
    reviews = list(reviews)
    known_findings = {finding.finding_id for finding in findings}

    reviews_by_finding: Dict[str, List[HumanReview]] = {}
    reviewer_keys = set()
    for review in reviews:
        if review.finding_id not in known_findings:
            raise ValueError(f"Review references unknown finding {review.finding_id}")
        reviewer_key = (review.finding_id, review.reviewer_id)
        if reviewer_key in reviewer_keys:
            raise ValueError(f"Duplicate reviewer {review.reviewer_id} for finding {review.finding_id}")
        reviewer_keys.add(reviewer_key)
        reviews_by_finding.setdefault(review.finding_id, []).append(review)

    approved: List[dict] = []
    payables: List[dict] = []
    unresolved: List[dict] = []

    for finding in findings:
        item = _jsonable_finding(finding)
        finding_reviews = reviews_by_finding.get(finding.finding_id, [])
        if finding.state == FindingState.RECOVERY_CANDIDATE:
            has_blocking_review = any(
                review.decision in {ReviewDecision.REJECTED, ReviewDecision.NEEDS_MORE_EVIDENCE}
                for review in finding_reviews
            )
            approval_count = sum(
                review.decision == ReviewDecision.APPROVED
                for review in finding_reviews
            )
            if not has_blocking_review and approval_count >= required_approvals:
                approved.append(item)
            else:
                unresolved.append(item)
        elif finding.state == FindingState.PAYABLE_CANDIDATE:
            payables.append(item)
        elif finding.state in {FindingState.UNKNOWN, FindingState.REQUIRES_REVIEW}:
            unresolved.append(item)

    if approved:
        status = PackStatus.READY_FOR_CLIENT_FINANCE_REVIEW
    elif any(f.state == FindingState.RECOVERY_CANDIDATE for f in findings):
        status = PackStatus.DRAFT
    else:
        status = PackStatus.NO_RECOVERY_PACK

    return RecoveryPack(
        organization_id=organization_id,
        status=status,
        approved_recovery_candidates=approved,
        payable_exposures=payables,
        unresolved=unresolved,
        review_log=[
            {
                "finding_id": r.finding_id,
                "reviewer_id": r.reviewer_id,
                "reviewer_role": r.reviewer_role,
                "decision": r.decision.value,
                "rationale": r.rationale,
                "reviewed_at": r.reviewed_at.isoformat(),
            }
            for r in reviews
        ],
    )
