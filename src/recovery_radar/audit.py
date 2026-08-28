from __future__ import annotations

import json


def tenant_audit_trail(storage, workspace_id: str) -> list[dict]:
    """Return an ordered tenant-scoped audit trail without cross-tenant rows."""
    rows = storage.conn.execute(
        "SELECT event_id,actor_id,entity_type,entity_id,action,payload,created_at "
        "FROM audit_events WHERE workspace_id=? ORDER BY event_id",
        (workspace_id,),
    ).fetchall()
    return [
        {
            "audit_event_id": int(row["event_id"]),
            "actor_id": row["actor_id"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "action": row["action"],
            "payload": json.loads(row["payload"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
