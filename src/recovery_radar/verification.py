from __future__ import annotations

import json
from typing import Literal

ReviewState = Literal["VERIFIED", "REJECTED"]


class _AppendOnlyReviewStore:
    table: str
    entity_column: str
    entity_table: str
    entity_type: str
    missing_error: str

    def __init__(self, storage):
        self.storage = storage
        self._migrate()

    def _migrate(self) -> None:
        self.storage.conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table}(
              review_id INTEGER PRIMARY KEY AUTOINCREMENT,
              workspace_id TEXT NOT NULL,
              {self.entity_column} TEXT NOT NULL,
              reviewer_actor_id TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN ('VERIFIED','REJECTED')),
              note TEXT NOT NULL DEFAULT '',
              reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(workspace_id, {self.entity_column})
                REFERENCES {self.entity_table}(workspace_id, {self.entity_column})
            );
            CREATE INDEX IF NOT EXISTS idx_{self.table}_current
              ON {self.table}(workspace_id, {self.entity_column}, review_id);
            """
        )
        self.storage.conn.commit()

    def _entity_exists(self, workspace_id: str, entity_id: str) -> bool:
        row = self.storage.conn.execute(
            f"SELECT 1 FROM {self.entity_table} WHERE workspace_id=? AND {self.entity_column}=?",
            (workspace_id, entity_id),
        ).fetchone()
        return row is not None

    def review(
        self,
        workspace_id: str,
        reviewer_actor_id: str,
        entity_id: str,
        state: ReviewState,
        note: str = "",
    ) -> None:
        if state not in {"VERIFIED", "REJECTED"}:
            raise ValueError("INVALID_REVIEW_STATE")
        if not self._entity_exists(workspace_id, entity_id):
            raise KeyError(self.missing_error)
        cursor = self.storage.conn.execute(
            f"INSERT INTO {self.table}(workspace_id,{self.entity_column},reviewer_actor_id,state,note) VALUES (?,?,?,?,?)",
            (workspace_id, entity_id, reviewer_actor_id, state, note),
        )
        review_id = int(cursor.lastrowid)
        payload = json.dumps(
            {"review_id": review_id, "state": state, "note": note},
            sort_keys=True,
        )
        self.storage.conn.execute(
            "INSERT INTO audit_events(workspace_id,actor_id,entity_type,entity_id,action,payload) VALUES (?,?,?,?,?,?)",
            (
                workspace_id,
                reviewer_actor_id,
                self.entity_type,
                entity_id,
                state,
                payload,
            ),
        )
        self.storage.conn.commit()

    def current_state(self, workspace_id: str, entity_id: str) -> str | None:
        row = self.storage.conn.execute(
            f"SELECT state FROM {self.table} WHERE workspace_id=? AND {self.entity_column}=? ORDER BY review_id DESC LIMIT 1",
            (workspace_id, entity_id),
        ).fetchone()
        return row["state"] if row is not None else None

    def verified_ids(self, workspace_id: str) -> set[str]:
        rows = self.storage.conn.execute(
            f"""
            SELECT r.{self.entity_column} AS entity_id, r.state
            FROM {self.table} r
            JOIN (
              SELECT {self.entity_column}, MAX(review_id) AS max_review_id
              FROM {self.table}
              WHERE workspace_id=?
              GROUP BY {self.entity_column}
            ) latest ON latest.max_review_id = r.review_id
            WHERE r.workspace_id=?
            """,
            (workspace_id, workspace_id),
        ).fetchall()
        return {row["entity_id"] for row in rows if row["state"] == "VERIFIED"}

    def history(self, workspace_id: str, entity_id: str) -> list[dict]:
        rows = self.storage.conn.execute(
            f"SELECT review_id,reviewer_actor_id,state,note,reviewed_at FROM {self.table} WHERE workspace_id=? AND {self.entity_column}=? ORDER BY review_id",
            (workspace_id, entity_id),
        ).fetchall()
        return [dict(row) for row in rows]


class EvidenceReviewStore(_AppendOnlyReviewStore):
    table = "evidence_reviews"
    entity_column = "document_id"
    entity_table = "evidence_documents"
    entity_type = "EVIDENCE_REVIEW"
    missing_error = "EVIDENCE_DOCUMENT_NOT_FOUND"

    def verified_document_ids(self, workspace_id: str) -> set[str]:
        return self.verified_ids(workspace_id)


class EntitlementReviewStore(_AppendOnlyReviewStore):
    table = "entitlement_reviews"
    entity_column = "entitlement_id"
    entity_table = "entitlement_bases"
    entity_type = "ENTITLEMENT_REVIEW"
    missing_error = "ENTITLEMENT_BASIS_NOT_FOUND"

    def verified_entitlement_ids(self, workspace_id: str) -> set[str]:
        return self.verified_ids(workspace_id)
