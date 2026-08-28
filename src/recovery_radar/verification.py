from __future__ import annotations

import json
from typing import Literal

ReviewState = Literal["VERIFIED", "REJECTED"]


class EvidenceReviewStore:
    """Append-only reviewer attestations for registered evidence documents."""

    def __init__(self, storage):
        self.storage = storage
        self._migrate()

    def _migrate(self) -> None:
        self.storage.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS evidence_reviews(
              review_id INTEGER PRIMARY KEY AUTOINCREMENT,
              workspace_id TEXT NOT NULL,
              document_id TEXT NOT NULL,
              reviewer_actor_id TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN ('VERIFIED','REJECTED')),
              note TEXT NOT NULL DEFAULT '',
              reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(workspace_id, document_id)
                REFERENCES evidence_documents(workspace_id, document_id)
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_reviews_current
              ON evidence_reviews(workspace_id, document_id, review_id);
            """
        )
        self.storage.conn.commit()

    def review(
        self,
        workspace_id: str,
        reviewer_actor_id: str,
        document_id: str,
        state: ReviewState,
        note: str = "",
    ) -> None:
        if state not in {"VERIFIED", "REJECTED"}:
            raise ValueError("INVALID_EVIDENCE_REVIEW_STATE")
        document = self.storage.get_evidence_document(workspace_id, document_id)
        if document is None:
            raise KeyError("EVIDENCE_DOCUMENT_NOT_FOUND")
        cursor = self.storage.conn.execute(
            "INSERT INTO evidence_reviews(workspace_id,document_id,reviewer_actor_id,state,note) VALUES (?,?,?,?,?)",
            (workspace_id, document_id, reviewer_actor_id, state, note),
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
                "EVIDENCE_REVIEW",
                document_id,
                state,
                payload,
            ),
        )
        self.storage.conn.commit()

    def current_state(self, workspace_id: str, document_id: str) -> str | None:
        row = self.storage.conn.execute(
            "SELECT state FROM evidence_reviews WHERE workspace_id=? AND document_id=? ORDER BY review_id DESC LIMIT 1",
            (workspace_id, document_id),
        ).fetchone()
        return row["state"] if row is not None else None

    def verified_document_ids(self, workspace_id: str) -> set[str]:
        rows = self.storage.conn.execute(
            """
            SELECT r.document_id, r.state
            FROM evidence_reviews r
            JOIN (
              SELECT document_id, MAX(review_id) AS max_review_id
              FROM evidence_reviews
              WHERE workspace_id=?
              GROUP BY document_id
            ) latest ON latest.max_review_id = r.review_id
            WHERE r.workspace_id=?
            """,
            (workspace_id, workspace_id),
        ).fetchall()
        return {row["document_id"] for row in rows if row["state"] == "VERIFIED"}

    def history(self, workspace_id: str, document_id: str) -> list[dict]:
        rows = self.storage.conn.execute(
            "SELECT review_id,reviewer_actor_id,state,note,reviewed_at FROM evidence_reviews WHERE workspace_id=? AND document_id=? ORDER BY review_id",
            (workspace_id, document_id),
        ).fetchall()
        return [dict(row) for row in rows]
