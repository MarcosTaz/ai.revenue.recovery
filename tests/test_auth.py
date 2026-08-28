import pytest

from recovery_radar.auth import AuthService
from recovery_radar.storage import Storage


def test_workspace_admin_bootstrap_authenticates_to_server_derived_tenant_and_role(tmp_path):
    store = Storage(tmp_path / "auth.db")
    try:
        store.create_workspace("A", "Supplier A")
        auth = AuthService(store)
        token = auth.bootstrap_workspace_admin("A", "alice")
        principal = auth.authenticate(token)
        assert principal.workspace_id == "A"
        assert principal.actor_id == "alice"
        assert principal.role == "ADMIN"
    finally:
        store.close()


def test_raw_api_secret_is_not_persisted(tmp_path):
    store = Storage(tmp_path / "auth.db")
    try:
        store.create_workspace("A", "Supplier A")
        auth = AuthService(store)
        token = auth.bootstrap_workspace_admin("A", "alice")
        key_id = auth.key_id_from_token(token)
        secret = token.split(".", 1)[1]
        row = store.conn.execute(
            "SELECT key_id,salt,secret_hash FROM api_credentials WHERE key_id=?", (key_id,)
        ).fetchone()
        assert row["key_id"] == key_id
        assert secret.encode() not in bytes(row["salt"])
        assert secret.encode() not in bytes(row["secret_hash"])
        assert token.encode() not in bytes(row["secret_hash"])
    finally:
        store.close()


def test_wrong_or_tampered_secret_fails_closed(tmp_path):
    store = Storage(tmp_path / "auth.db")
    try:
        store.create_workspace("A", "Supplier A")
        auth = AuthService(store)
        token = auth.bootstrap_workspace_admin("A", "alice")
        key_id, secret = token.split(".", 1)
        replacement = "A" if secret[-1] != "A" else "B"
        with pytest.raises(PermissionError, match="INVALID_API_KEY"):
            auth.authenticate(f"{key_id}.{secret[:-1]}{replacement}")
        with pytest.raises(PermissionError, match="INVALID_API_KEY"):
            auth.authenticate("not-a-key")
    finally:
        store.close()


def test_bootstrap_is_one_time_and_non_admin_cannot_issue_keys(tmp_path):
    store = Storage(tmp_path / "auth.db")
    try:
        store.create_workspace("A", "Supplier A")
        auth = AuthService(store)
        admin = auth.bootstrap_workspace_admin("A", "alice")
        with pytest.raises(PermissionError, match="ALREADY_BOOTSTRAPPED"):
            auth.bootstrap_workspace_admin("A", "mallory")
        analyst = auth.issue_key(admin, "analyst-1", "ANALYST")
        assert auth.authenticate(analyst).role == "ANALYST"
        with pytest.raises(PermissionError, match="ADMIN_REQUIRED_FOR_KEY_ISSUE"):
            auth.issue_key(analyst, "reviewer-1", "REVIEWER")
    finally:
        store.close()


def test_revoked_key_cannot_authenticate(tmp_path):
    store = Storage(tmp_path / "auth.db")
    try:
        store.create_workspace("A", "Supplier A")
        auth = AuthService(store)
        admin = auth.bootstrap_workspace_admin("A", "alice")
        analyst = auth.issue_key(admin, "analyst-1", "ANALYST")
        key_id = auth.key_id_from_token(analyst)
        auth.revoke_key(admin, key_id)
        with pytest.raises(PermissionError, match="INVALID_API_KEY"):
            auth.authenticate(analyst)
    finally:
        store.close()


def test_admin_cannot_revoke_key_from_other_tenant(tmp_path):
    store = Storage(tmp_path / "auth.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        auth = AuthService(store)
        admin_a = auth.bootstrap_workspace_admin("A", "alice")
        admin_b = auth.bootstrap_workspace_admin("B", "bob")
        analyst_b = auth.issue_key(admin_b, "b-analyst", "ANALYST")
        with pytest.raises(KeyError, match="API_KEY_NOT_FOUND"):
            auth.revoke_key(admin_a, auth.key_id_from_token(analyst_b))
        assert auth.authenticate(analyst_b).workspace_id == "B"
    finally:
        store.close()
