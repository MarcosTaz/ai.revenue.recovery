from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from .workflow import ClaimCase, PaymentRecord


class Storage:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self) -> None:
        self.conn.close()

    def _migrate(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspaces(
              workspace_id TEXT PRIMARY KEY,
              name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claim_cases(
              workspace_id TEXT NOT NULL,
              case_id TEXT NOT NULL,
              payload TEXT NOT NULL,
              PRIMARY KEY(workspace_id, case_id),
              FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
            );
            CREATE TABLE IF NOT EXISTS audit_events(
              event_id INTEGER PRIMARY KEY AUTOINCREMENT,
              workspace_id TEXT NOT NULL,
              actor_id TEXT NOT NULL,
              entity_type TEXT NOT NULL,
              entity_id TEXT NOT NULL,
              action TEXT NOT NULL,
              payload TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
            );
            """
        )
        self.conn.commit()

    def create_workspace(self, workspace_id: str, name: str) -> None:
        if not workspace_id.strip() or not name.strip():
            raise ValueError("WORKSPACE_REQUIRED")
        self.conn.execute(
            "INSERT INTO workspaces(workspace_id,name) VALUES (?,?)",
            (workspace_id, name),
        )
        self.conn.commit()

    def _workspace_exists(self, workspace_id: str) -> None:
        row = self.conn.execute(
            "SELECT 1 FROM workspaces WHERE workspace_id=?", (workspace_id,)
        ).fetchone()
        if row is None:
            raise KeyError("WORKSPACE_NOT_FOUND")

    @staticmethod
    def _serialize_case(case: ClaimCase) -> dict:
        return {
            **asdict(case),
            "claim_amount": str(case.claim_amount),
            "settled_amount": str(case.settled_amount),
            "payments": [
                {**asdict(payment), "amount": str(payment.amount)}
                for payment in case.payments
            ],
        }

    def put_claim_case(self, workspace_id: str, actor_id: str, case: ClaimCase) -> None:
        self._workspace_exists(workspace_id)
        if case.workspace_id != workspace_id:
            raise ValueError("CLAIM_CASE_WORKSPACE_MISMATCH")
        payload = self._serialize_case(case)
        raw = json.dumps(payload, sort_keys=True)
        self.conn.execute(
            "INSERT OR REPLACE INTO claim_cases(workspace_id,case_id,payload) VALUES (?,?,?)",
            (workspace_id, case.case_id, raw),
        )
        self.conn.execute(
            "INSERT INTO audit_events(workspace_id,actor_id,entity_type,entity_id,action,payload) VALUES (?,?,?,?,?,?)",
            (workspace_id, actor_id, "CLAIM_CASE", case.case_id, "UPSERT", raw),
        )
        self.conn.commit()

    def get_claim_case(self, workspace_id: str, case_id: str) -> ClaimCase | None:
        self._workspace_exists(workspace_id)
        row = self.conn.execute(
            "SELECT payload FROM claim_cases WHERE workspace_id=? AND case_id=?",
            (workspace_id, case_id),
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload"])
        payments = tuple(
            PaymentRecord(
                item["payment_id"],
                Decimal(item["amount"]),
                item["currency"],
                item["payment_evidence_ref"],
            )
            for item in payload["payments"]
        )
        return ClaimCase(
            payload["case_id"],
            payload["workspace_id"],
            Decimal(payload["claim_amount"]),
            payload["currency"],
            payload["state"],
            Decimal(payload["settled_amount"]),
            payload["settlement_evidence_ref"],
            payments,
        )

    def audit_count(self, workspace_id: str) -> int:
        self._workspace_exists(workspace_id)
        row = self.conn.execute(
            "SELECT COUNT(*) n FROM audit_events WHERE workspace_id=?", (workspace_id,)
        ).fetchone()
        return int(row["n"])

    def backup_to(self, destination: str | Path) -> None:
        target = sqlite3.connect(str(destination))
        try:
            self.conn.backup(target)
        finally:
            target.close()

    def economic_digest(self, workspace_id: str) -> str:
        import hashlib

        self._workspace_exists(workspace_id)
        rows = [
            row["payload"]
            for row in self.conn.execute(
                "SELECT payload FROM claim_cases WHERE workspace_id=? ORDER BY case_id",
                (workspace_id,),
            ).fetchall()
        ]
        return hashlib.sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest()
