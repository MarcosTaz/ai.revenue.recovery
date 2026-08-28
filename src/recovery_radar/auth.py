from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from typing import Literal

Role = Literal["ADMIN", "ANALYST", "REVIEWER"]
_ALLOWED_ROLES = {"ADMIN", "ANALYST", "REVIEWER"}
_TOKEN_RE = re.compile(r"^rrk_([A-Za-z0-9_-]{12,64})\.([A-Za-z0-9_-]{32,128})$")


@dataclass(frozen=True, slots=True)
class Principal:
    workspace_id: str
    actor_id: str
    role: Role


def _parse_token(token: str) -> tuple[str, str]:
    match = _TOKEN_RE.fullmatch(token or "")
    if match is None:
        raise PermissionError("INVALID_API_KEY")
    return match.group(1), match.group(2)


def _derive_secret(secret: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", secret.encode("utf-8"), salt, 310_000, dklen=32
    )


class AuthService:
    """Minimal authenticated identity boundary for assisted pilot operation.

    API key secrets are returned once and never persisted raw. The database keeps
    only a random salt and PBKDF2-HMAC-SHA256 derived secret. Workspace scope and
    role are recovered from the credential record, not from caller input.

    This is an application authentication boundary, not a claim of complete
    production IAM (SSO, MFA, account recovery, rate limiting, etc.).
    """

    def __init__(self, storage):
        self.storage = storage
        self._migrate()

    def _migrate(self) -> None:
        self.storage.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS api_credentials(
              key_id TEXT PRIMARY KEY,
              workspace_id TEXT NOT NULL,
              actor_id TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('ADMIN','ANALYST','REVIEWER')),
              salt BLOB NOT NULL,
              secret_hash BLOB NOT NULL,
              revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN (0,1)),
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
            );
            CREATE INDEX IF NOT EXISTS idx_api_credentials_workspace
              ON api_credentials(workspace_id);
            """
        )
        self.storage.conn.commit()

    def _workspace_exists(self, workspace_id: str) -> None:
        row = self.storage.conn.execute(
            "SELECT 1 FROM workspaces WHERE workspace_id=?", (workspace_id,)
        ).fetchone()
        if row is None:
            raise KeyError("WORKSPACE_NOT_FOUND")

    def _new_key(self, workspace_id: str, actor_id: str, role: Role) -> str:
        if role not in _ALLOWED_ROLES:
            raise ValueError("INVALID_ROLE")
        if not actor_id.strip():
            raise ValueError("ACTOR_ID_REQUIRED")
        self._workspace_exists(workspace_id)
        key_id = secrets.token_urlsafe(12)
        secret = secrets.token_urlsafe(32)
        salt = secrets.token_bytes(16)
        secret_hash = _derive_secret(secret, salt)
        self.storage.conn.execute(
            "INSERT INTO api_credentials(key_id,workspace_id,actor_id,role,salt,secret_hash) VALUES (?,?,?,?,?,?)",
            (key_id, workspace_id, actor_id, role, salt, secret_hash),
        )
        self.storage.conn.commit()
        return f"rrk_{key_id}.{secret}"

    def bootstrap_workspace_admin(self, workspace_id: str, actor_id: str) -> str:
        """One-time local/operator bootstrap for a workspace's first admin."""
        self._workspace_exists(workspace_id)
        count = self.storage.conn.execute(
            "SELECT COUNT(*) n FROM api_credentials WHERE workspace_id=?",
            (workspace_id,),
        ).fetchone()["n"]
        if count:
            raise PermissionError("WORKSPACE_AUTH_ALREADY_BOOTSTRAPPED")
        return self._new_key(workspace_id, actor_id, "ADMIN")

    def authenticate(self, token: str) -> Principal:
        key_id, secret = _parse_token(token)
        row = self.storage.conn.execute(
            "SELECT workspace_id,actor_id,role,salt,secret_hash,revoked FROM api_credentials WHERE key_id=?",
            (key_id,),
        ).fetchone()
        if row is None or row["revoked"]:
            raise PermissionError("INVALID_API_KEY")
        actual = _derive_secret(secret, bytes(row["salt"]))
        if not hmac.compare_digest(actual, bytes(row["secret_hash"])):
            raise PermissionError("INVALID_API_KEY")
        return Principal(row["workspace_id"], row["actor_id"], row["role"])

    def issue_key(self, admin_token: str, actor_id: str, role: Role) -> str:
        admin = self.authenticate(admin_token)
        if admin.role != "ADMIN":
            raise PermissionError("ADMIN_REQUIRED_FOR_KEY_ISSUE")
        return self._new_key(admin.workspace_id, actor_id, role)

    def revoke_key(self, admin_token: str, key_id: str) -> None:
        admin = self.authenticate(admin_token)
        if admin.role != "ADMIN":
            raise PermissionError("ADMIN_REQUIRED_FOR_KEY_REVOKE")
        row = self.storage.conn.execute(
            "SELECT workspace_id FROM api_credentials WHERE key_id=?", (key_id,)
        ).fetchone()
        if row is None or row["workspace_id"] != admin.workspace_id:
            raise KeyError("API_KEY_NOT_FOUND")
        self.storage.conn.execute(
            "UPDATE api_credentials SET revoked=1 WHERE key_id=?", (key_id,)
        )
        self.storage.conn.commit()

    @staticmethod
    def key_id_from_token(token: str) -> str:
        key_id, _ = _parse_token(token)
        return key_id
