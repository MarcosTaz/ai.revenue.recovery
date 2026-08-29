from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class AuthorizationError(PermissionError):
    pass


class Role(str, Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"


class Action(str, Enum):
    READ = "READ"
    IMPORT = "IMPORT"
    RUN_AUDIT = "RUN_AUDIT"
    REVIEW_FINDING = "REVIEW_FINDING"
    MANAGE_MEMBERS = "MANAGE_MEMBERS"


_ALLOWED = {
    Role.ADMIN: frozenset(Action),
    Role.ANALYST: frozenset({Action.READ, Action.IMPORT, Action.RUN_AUDIT}),
    Role.REVIEWER: frozenset({Action.READ, Action.REVIEW_FINDING}),
    Role.VIEWER: frozenset({Action.READ}),
}


@dataclass(frozen=True)
class OrganizationMember:
    organization_id: str
    user_id: str
    role: Role
    active: bool = True

    def __post_init__(self):
        if not self.organization_id.strip() or not self.user_id.strip():
            raise ValueError("organization_id and user_id are required")


def authorize(
    organization_id: str,
    user_id: str,
    action: Action,
    memberships: Iterable[OrganizationMember],
) -> OrganizationMember:
    matches = [
        membership
        for membership in memberships
        if membership.organization_id == organization_id
        and membership.user_id == user_id
        and membership.active
    ]
    if len(matches) != 1:
        raise AuthorizationError("No unique active organization membership")
    membership = matches[0]
    if action not in _ALLOWED[membership.role]:
        raise AuthorizationError(f"Role {membership.role.value} is not authorized for {action.value}")
    return membership


def assert_same_organization(expected_organization_id: str, actual_organization_id: str) -> None:
    if expected_organization_id != actual_organization_id:
        raise AuthorizationError("Cross-tenant resource access denied")
