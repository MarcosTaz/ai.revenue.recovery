from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .authz import Action, OrganizationMember, authorize


class SessionAuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class VerifiedSession:
    session_id: str
    user_id: str
    issued_at: datetime
    expires_at: datetime
    issuer: str
    cryptographically_verified: bool

    def __post_init__(self):
        if not self.session_id.strip() or not self.user_id.strip() or not self.issuer.strip():
            raise ValueError("session identity fields are required")
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("session timestamps must be timezone-aware")
        if self.expires_at <= self.issued_at:
            raise ValueError("session expiry must be after issuance")


def authorize_session(
    session: VerifiedSession,
    organization_id: str,
    action: Action,
    memberships: Iterable[OrganizationMember],
    now: datetime,
) -> OrganizationMember:
    """Bind a verified session identity to the existing organization authorization model.

    The cryptographic verification itself must be performed by a production IdP/
    session layer. A caller-supplied user id is never enough.
    """
    if now.tzinfo is None:
        raise ValueError("authorization time must be timezone-aware")
    if not session.cryptographically_verified:
        raise SessionAuthorizationError("unverified session cannot authorize protected operations")
    if now < session.issued_at:
        raise SessionAuthorizationError("session is not yet valid")
    if now >= session.expires_at:
        raise SessionAuthorizationError("session has expired")
    try:
        return authorize(organization_id, session.user_id, action, memberships)
    except PermissionError as exc:
        raise SessionAuthorizationError(str(exc)) from exc
