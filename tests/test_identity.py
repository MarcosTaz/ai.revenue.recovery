from datetime import datetime, timedelta, timezone

from govmargin.authz import Action, OrganizationMember, Role
from govmargin.identity import SessionAuthorizationError, VerifiedSession, authorize_session


NOW = datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc)


def _session(user_id="analyst-1", verified=True, issued=None, expires=None):
    return VerifiedSession(
        session_id="session-1",
        user_id=user_id,
        issued_at=issued or (NOW - timedelta(minutes=5)),
        expires_at=expires or (NOW + timedelta(hours=1)),
        issuer="test-idp",
        cryptographically_verified=verified,
    )


def test_verified_session_binds_identity_to_tenant_membership():
    membership = OrganizationMember("org-a", "analyst-1", Role.ANALYST)
    authorized = authorize_session(_session(), "org-a", Action.RUN_AUDIT, [membership], NOW)
    assert authorized == membership


def test_unverified_expired_or_future_session_fails_closed():
    membership = OrganizationMember("org-a", "analyst-1", Role.ANALYST)
    for session in (
        _session(verified=False),
        _session(issued=NOW - timedelta(hours=2), expires=NOW - timedelta(seconds=1)),
        _session(issued=NOW + timedelta(minutes=1), expires=NOW + timedelta(hours=1)),
    ):
        try:
            authorize_session(session, "org-a", Action.RUN_AUDIT, [membership], NOW)
        except SessionAuthorizationError:
            pass
        else:
            raise AssertionError("invalid session must fail closed")


def test_verified_identity_cannot_cross_tenant_or_escalate_role():
    memberships = [
        OrganizationMember("org-a", "analyst-1", Role.ANALYST),
        OrganizationMember("org-b", "viewer-1", Role.VIEWER),
    ]
    try:
        authorize_session(_session(), "org-b", Action.RUN_AUDIT, memberships, NOW)
    except SessionAuthorizationError:
        pass
    else:
        raise AssertionError("cross-tenant identity must be denied")

    viewer = _session(user_id="viewer-1")
    try:
        authorize_session(viewer, "org-b", Action.RUN_AUDIT, memberships, NOW)
    except SessionAuthorizationError:
        pass
    else:
        raise AssertionError("viewer must not escalate to audit execution")
