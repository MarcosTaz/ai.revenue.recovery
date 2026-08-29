from __future__ import annotations

import sqlite3
from typing import Any

APPLICATION_SCHEMA_VERSION = 1

_REQUIRED_COLUMNS: dict[str, set[str]] = {
    "workspaces": {"workspace_id", "name"},
    "recovery_events": {"workspace_id", "event_id", "payload"},
    "exposure_lines": {"workspace_id", "exposure_id", "event_id", "payload"},
    "entitlement_bases": {
        "workspace_id",
        "entitlement_id",
        "event_id",
        "economic_loss_id",
        "payload",
    },
    "claim_cases": {"workspace_id", "case_id", "payload"},
    "evidence_documents": {
        "workspace_id",
        "document_id",
        "content_sha256",
        "payload",
    },
    "audit_events": {
        "event_id",
        "workspace_id",
        "actor_id",
        "entity_type",
        "entity_id",
        "action",
        "payload",
        "created_at",
    },
    "api_credentials": {
        "key_id",
        "workspace_id",
        "actor_id",
        "role",
        "salt",
        "secret_hash",
        "revoked",
        "created_at",
    },
    "evidence_reviews": {
        "review_id",
        "workspace_id",
        "document_id",
        "reviewer_actor_id",
        "state",
        "note",
        "reviewed_at",
    },
    "entitlement_reviews": {
        "review_id",
        "workspace_id",
        "entitlement_id",
        "reviewer_actor_id",
        "state",
        "note",
        "reviewed_at",
    },
}


class SchemaCompatibilityError(RuntimeError):
    pass


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    safe = table.replace('"', '""')
    return {
        row[1]
        for row in conn.execute(f'PRAGMA table_info("{safe}")').fetchall()
    }


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def validate_application_schema(storage) -> dict[str, Any]:
    """Refuse startup when persisted application truth has an unknown shape.

    This is intentionally conservative. It does not auto-transform existing
    economic records. A future migration must explicitly understand both schema
    versions before changing persisted truth.
    """
    conn = storage.conn
    tables = _table_names(conn)
    issues: list[str] = []
    for table, required in sorted(_REQUIRED_COLUMNS.items()):
        if table not in tables:
            issues.append(f"MISSING_TABLE:{table}")
            continue
        missing = sorted(required - _columns(conn, table))
        if missing:
            issues.append(f"MISSING_COLUMNS:{table}:{','.join(missing)}")
    if issues:
        raise SchemaCompatibilityError("APPLICATION_SCHEMA_INCOMPATIBLE:" + "|".join(issues))

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS application_schema_metadata(
          singleton INTEGER PRIMARY KEY CHECK(singleton=1),
          schema_version INTEGER NOT NULL
        )
        """
    )
    row = conn.execute(
        "SELECT schema_version FROM application_schema_metadata WHERE singleton=1"
    ).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO application_schema_metadata(singleton,schema_version) VALUES (1,?)",
            (APPLICATION_SCHEMA_VERSION,),
        )
        conn.commit()
        version = APPLICATION_SCHEMA_VERSION
    else:
        version = int(row[0])
        if version > APPLICATION_SCHEMA_VERSION:
            conn.rollback()
            raise SchemaCompatibilityError(
                f"DATABASE_SCHEMA_NEWER_THAN_APPLICATION:{version}>{APPLICATION_SCHEMA_VERSION}"
            )
        if version < APPLICATION_SCHEMA_VERSION:
            conn.rollback()
            raise SchemaCompatibilityError(
                f"EXPLICIT_MIGRATION_REQUIRED:{version}->{APPLICATION_SCHEMA_VERSION}"
            )

    return {
        "schema_version": version,
        "required_table_count": len(_REQUIRED_COLUMNS),
        "state": "COMPATIBLE",
    }
