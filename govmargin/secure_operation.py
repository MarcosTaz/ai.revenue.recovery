from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .authz import Action, OrganizationMember, authorize
from .operation import AuditOperationResult, run_normalized_indirect_audit
from .review import HumanReview


class ReviewAuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class AuthorizedAuditContext:
    organization_id: str
    actor_user_id: str


def _validate_review_authorization(
    organization_id: str,
    reviews: Sequence[HumanReview],
    memberships: Iterable[OrganizationMember],
) -> None:
    membership_list = list(memberships)
    for review in reviews:
        try:
            membership = authorize(
                organization_id,
                review.reviewer_id,
                Action.REVIEW_FINDING,
                membership_list,
            )
        except PermissionError as exc:
            raise ReviewAuthorizationError(
                f"Reviewer {review.reviewer_id} is not authorized for organization {organization_id}"
            ) from exc
        if membership.role.value != review.reviewer_role:
            raise ReviewAuthorizationError(
                f"Reviewer role mismatch for {review.reviewer_id}: signed={review.reviewer_role} membership={membership.role.value}"
            )


def run_authorized_normalized_indirect_audit(
    bundle: Mapping[str, object],
    actor_user_id: str,
    memberships: Iterable[OrganizationMember],
    reviews: Sequence[HumanReview] = (),
) -> AuditOperationResult:
    organization_id = str(bundle.get("organization_id", "")).strip()
    membership_list = list(memberships)
    authorize(organization_id, actor_user_id, Action.RUN_AUDIT, membership_list)
    _validate_review_authorization(organization_id, reviews, membership_list)
    return run_normalized_indirect_audit(bundle, reviews)
