from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from .evidence import EvidenceDocument
from .models import EntitlementBasis, ExposureLine, RecoveryEvent
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
            CREATE TABLE IF NOT EXISTS recovery_events(
              workspace_id TEXT NOT NULL,
              event_id TEXT NOT NULL,
              payload TEXT NOT NULL,
              PRIMARY KEY(workspace_id, event_id),
              FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
            );
            CREATE TABLE IF NOT EXISTS exposure_lines(
              workspace_id TEXT NOT NULL,
              exposure_id TEXT NOT NULL,
              event_id TEXT NOT NULL,
              payload TEXT NOT NULL,
              PRIMARY KEY(workspace_id, exposure_id),
              FOREIGN KEY(workspace_id, event_id) REFERENCES recovery_events(workspace_id, event_id)
            );
            CREATE TABLE IF NOT EXISTS entitlement_bases(
              workspace_id TEXT NOT NULL,
              entitlement_id TEXT NOT NULL,
              event_id TEXT NOT NULL,
              economic_loss_id TEXT NOT NULL,
              payload TEXT NOT NULL,
              PRIMARY KEY(workspace_id, entitlement_id),
              FOREIGN KEY(workspace_id, event_id) REFERENCES recovery_events(workspace_id, event_id)
            );
            CREATE TABLE IF NOT EXISTS claim_cases(
              workspace_id TEXT NOT NULL,
              case_id TEXT NOT NULL,
              payload TEXT NOT NULL,
              PRIMARY KEY(workspace_id, case_id),
              FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
            );
            CREATE TABLE IF NOT EXISTS evidence_documents(
              workspace_id TEXT NOT NULL,
              document_id TEXT NOT NULL,
              content_sha256 TEXT NOT NULL,
              payload TEXT NOT NULL,
              PRIMARY KEY(workspace_id, document_id),
              UNIQUE(workspace_id, content_sha256),
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
    def _serialize_event(event: RecoveryEvent) -> dict:
        return {
            **asdict(event),
            "event_date": event.event_date.isoformat(),
            "expected_volume": str(event.expected_volume),
            "revised_volume": str(event.revised_volume),
        }

    @staticmethod
    def _serialize_exposure(line: ExposureLine) -> dict:
        return {
            **asdict(line),
            "quantity": str(line.quantity),
            "unit_cost": str(line.unit_cost),
            "mitigation_amount": str(line.mitigation_amount),
            "already_reimbursed_amount": str(line.already_reimbursed_amount),
        }

    @staticmethod
    def _serialize_entitlement(basis: EntitlementBasis) -> dict:
        return {
            **asdict(basis),
            "recoverable_cap": str(basis.recoverable_cap)
            if basis.recoverable_cap is not None
            else None,
        }

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
            "selected_exposure_ids": list(case.selected_exposure_ids),
        }

    @staticmethod
    def _serialize_document(document: EvidenceDocument) -> dict:
        return {
            **asdict(document),
            "document_date": document.document_date.isoformat()
            if document.document_date
            else None,
        }

    def _audit(
        self,
        workspace_id: str,
        actor_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict,
    ) -> None:
        self.conn.execute(
            "INSERT INTO audit_events(workspace_id,actor_id,entity_type,entity_id,action,payload) VALUES (?,?,?,?,?,?)",
            (
                workspace_id,
                actor_id,
                entity_type,
                entity_id,
                action,
                json.dumps(payload, sort_keys=True),
            ),
        )

    def _insert_immutable(
        self,
        *,
        table: str,
        workspace_id: str,
        id_column: str,
        entity_id: str,
        payload: dict,
        actor_id: str,
        entity_type: str,
        extra_columns: tuple[str, ...] = (),
        extra_values: tuple[str, ...] = (),
    ) -> None:
        self._workspace_exists(workspace_id)
        raw = json.dumps(payload, sort_keys=True)
        existing = self.conn.execute(
            f"SELECT payload FROM {table} WHERE workspace_id=? AND {id_column}=?",
            (workspace_id, entity_id),
        ).fetchone()
        if existing is not None:
            if existing["payload"] == raw:
                return
            raise ValueError(f"{entity_type}_ID_CONFLICT")
        columns = ("workspace_id", id_column, *extra_columns, "payload")
        placeholders = ",".join("?" for _ in columns)
        self.conn.execute(
            f"INSERT INTO {table}({','.join(columns)}) VALUES ({placeholders})",
            (workspace_id, entity_id, *extra_values, raw),
        )
        self._audit(workspace_id, actor_id, entity_type, entity_id, "CREATE", payload)
        self.conn.commit()

    def put_recovery_event(
        self, workspace_id: str, actor_id: str, event: RecoveryEvent
    ) -> None:
        self._insert_immutable(
            table="recovery_events",
            workspace_id=workspace_id,
            id_column="event_id",
            entity_id=event.event_id,
            payload=self._serialize_event(event),
            actor_id=actor_id,
            entity_type="RECOVERY_EVENT",
        )

    def get_recovery_event(
        self, workspace_id: str, event_id: str
    ) -> RecoveryEvent | None:
        self._workspace_exists(workspace_id)
        row = self.conn.execute(
            "SELECT payload FROM recovery_events WHERE workspace_id=? AND event_id=?",
            (workspace_id, event_id),
        ).fetchone()
        if row is None:
            return None
        p = json.loads(row["payload"])
        return RecoveryEvent(
            p["event_id"], p["customer_id"], p["program_id"], p["part_id"],
            p["event_type"], date.fromisoformat(p["event_date"]),
            Decimal(p["expected_volume"]), Decimal(p["revised_volume"]),
            p["source_ref"], p["evidence_ref"]
        )

    def put_exposure_line(
        self, workspace_id: str, actor_id: str, line: ExposureLine
    ) -> None:
        if self.get_recovery_event(workspace_id, line.event_id) is None:
            raise KeyError("PARENT_EVENT_NOT_FOUND")
        self._insert_immutable(
            table="exposure_lines",
            workspace_id=workspace_id,
            id_column="exposure_id",
            entity_id=line.exposure_id,
            payload=self._serialize_exposure(line),
            actor_id=actor_id,
            entity_type="EXPOSURE_LINE",
            extra_columns=("event_id",),
            extra_values=(line.event_id,),
        )

    def get_exposure_line(
        self, workspace_id: str, exposure_id: str
    ) -> ExposureLine | None:
        self._workspace_exists(workspace_id)
        row = self.conn.execute(
            "SELECT payload FROM exposure_lines WHERE workspace_id=? AND exposure_id=?",
            (workspace_id, exposure_id),
        ).fetchone()
        if row is None:
            return None
        p = json.loads(row["payload"])
        return ExposureLine(
            p["exposure_id"], p["event_id"], p["economic_loss_id"], p["category"],
            Decimal(p["quantity"]), Decimal(p["unit_cost"]), p["currency"],
            p["inventory_or_cost_ref"], p["ownership"], Decimal(p["mitigation_amount"]),
            p["mitigation_evidence_ref"], Decimal(p["already_reimbursed_amount"]),
            p["reimbursement_evidence_ref"]
        )

    def list_exposure_lines(
        self, workspace_id: str, event_id: str
    ) -> list[ExposureLine]:
        self._workspace_exists(workspace_id)
        rows = self.conn.execute(
            "SELECT exposure_id FROM exposure_lines WHERE workspace_id=? AND event_id=? ORDER BY exposure_id",
            (workspace_id, event_id),
        ).fetchall()
        return [self.get_exposure_line(workspace_id, row["exposure_id"]) for row in rows]

    def put_entitlement_basis(
        self, workspace_id: str, actor_id: str, basis: EntitlementBasis
    ) -> None:
        if self.get_recovery_event(workspace_id, basis.event_id) is None:
            raise KeyError("PARENT_EVENT_NOT_FOUND")
        self._insert_immutable(
            table="entitlement_bases",
            workspace_id=workspace_id,
            id_column="entitlement_id",
            entity_id=basis.entitlement_id,
            payload=self._serialize_entitlement(basis),
            actor_id=actor_id,
            entity_type="ENTITLEMENT_BASIS",
            extra_columns=("event_id", "economic_loss_id"),
            extra_values=(basis.event_id, basis.economic_loss_id),
        )

    def get_entitlement_basis(
        self, workspace_id: str, entitlement_id: str
    ) -> EntitlementBasis | None:
        self._workspace_exists(workspace_id)
        row = self.conn.execute(
            "SELECT payload FROM entitlement_bases WHERE workspace_id=? AND entitlement_id=?",
            (workspace_id, entitlement_id),
        ).fetchone()
        if row is None:
            return None
        p = json.loads(row["payload"])
        return EntitlementBasis(
            p["entitlement_id"], p["event_id"], p["economic_loss_id"], p["support_state"],
            p["contractual_basis_ref"], p["supporting_document_ref"],
            Decimal(p["recoverable_cap"]) if p["recoverable_cap"] is not None else None,
            p["legal_review_required"]
        )

    def list_entitlement_bases(
        self, workspace_id: str, event_id: str
    ) -> list[EntitlementBasis]:
        self._workspace_exists(workspace_id)
        rows = self.conn.execute(
            "SELECT entitlement_id FROM entitlement_bases WHERE workspace_id=? AND event_id=? ORDER BY entitlement_id",
            (workspace_id, event_id),
        ).fetchall()
        return [self.get_entitlement_basis(workspace_id, row["entitlement_id"]) for row in rows]

    def put_claim_case(self, workspace_id: str, actor_id: str, case: ClaimCase) -> None:
        self._workspace_exists(workspace_id)
        if case.workspace_id != workspace_id:
            raise ValueError("CLAIM_CASE_WORKSPACE_MISMATCH")
        if not case.event_id or not case.analysis_fingerprint or not case.selected_exposure_ids:
            raise ValueError("CLAIM_CASE_PROVENANCE_REQUIRED")
        if self.get_recovery_event(workspace_id, case.event_id) is None:
            raise KeyError("CLAIM_CASE_EVENT_NOT_FOUND")
        for exposure_id in case.selected_exposure_ids:
            line = self.get_exposure_line(workspace_id, exposure_id)
            if line is None or line.event_id != case.event_id:
                raise ValueError("CLAIM_CASE_EXPOSURE_PROVENANCE_MISMATCH")
        payload = self._serialize_case(case)
        raw = json.dumps(payload, sort_keys=True)
        self.conn.execute(
            "INSERT OR REPLACE INTO claim_cases(workspace_id,case_id,payload) VALUES (?,?,?)",
            (workspace_id, case.case_id, raw),
        )
        self._audit(workspace_id, actor_id, "CLAIM_CASE", case.case_id, "UPSERT", payload)
        self.conn.commit()

    def get_claim_case(self, workspace_id: str, case_id: str) -> ClaimCase | None:
        self._workspace_exists(workspace_id)
        row = self.conn.execute(
            "SELECT payload FROM claim_cases WHERE workspace_id=? AND case_id=?",
            (workspace_id, case_id),
        ).fetchone()
        if row is None:
            return None
        p = json.loads(row["payload"])
        payments = tuple(
            PaymentRecord(
                item["payment_id"], Decimal(item["amount"]), item["currency"],
                item["payment_evidence_ref"],
            )
            for item in p["payments"]
        )
        return ClaimCase(
            case_id=p["case_id"], workspace_id=p["workspace_id"],
            claim_amount=Decimal(p["claim_amount"]), currency=p["currency"],
            state=p["state"], settled_amount=Decimal(p["settled_amount"]),
            settlement_evidence_ref=p["settlement_evidence_ref"], payments=payments,
            event_id=p.get("event_id", ""), analysis_fingerprint=p.get("analysis_fingerprint", ""),
            selected_exposure_ids=tuple(p.get("selected_exposure_ids", ())),
        )

    def put_evidence_document(
        self, workspace_id: str, actor_id: str, document: EvidenceDocument
    ) -> None:
        self._workspace_exists(workspace_id)
        if document.workspace_id != workspace_id:
            raise ValueError("EVIDENCE_DOCUMENT_WORKSPACE_MISMATCH")
        payload = self._serialize_document(document)
        raw = json.dumps(payload, sort_keys=True)
        existing = self.conn.execute(
            "SELECT payload FROM evidence_documents WHERE workspace_id=? AND document_id=?",
            (workspace_id, document.document_id),
        ).fetchone()
        if existing is not None:
            if existing["payload"] == raw:
                return
            raise ValueError("DOCUMENT_ID_VERSION_CONFLICT")
        duplicate = self.conn.execute(
            "SELECT document_id FROM evidence_documents WHERE workspace_id=? AND content_sha256=?",
            (workspace_id, document.content_sha256),
        ).fetchone()
        if duplicate is not None:
            raise ValueError(f"DUPLICATE_DOCUMENT_CONTENT:{duplicate['document_id']}")
        self.conn.execute(
            "INSERT INTO evidence_documents(workspace_id,document_id,content_sha256,payload) VALUES (?,?,?,?)",
            (workspace_id, document.document_id, document.content_sha256, raw),
        )
        self._audit(workspace_id, actor_id, "EVIDENCE_DOCUMENT", document.document_id, "CREATE", payload)
        self.conn.commit()

    def get_evidence_document(
        self, workspace_id: str, document_id: str
    ) -> EvidenceDocument | None:
        self._workspace_exists(workspace_id)
        row = self.conn.execute(
            "SELECT payload FROM evidence_documents WHERE workspace_id=? AND document_id=?",
            (workspace_id, document_id),
        ).fetchone()
        if row is None:
            return None
        p = json.loads(row["payload"])
        return EvidenceDocument(
            document_id=p["document_id"], workspace_id=p["workspace_id"],
            supplier_id=p["supplier_id"], customer_id=p["customer_id"],
            program_id=p["program_id"], evidence_type=p["evidence_type"], source_ref=p["source_ref"],
            version_id=p["version_id"], document_date=date.fromisoformat(p["document_date"]) if p["document_date"] else None,
            content_sha256=p["content_sha256"], signed=p["signed"],
        )

    def list_evidence_documents(self, workspace_id: str) -> list[EvidenceDocument]:
        self._workspace_exists(workspace_id)
        rows = self.conn.execute(
            "SELECT document_id FROM evidence_documents WHERE workspace_id=? ORDER BY document_id",
            (workspace_id,),
        ).fetchall()
        return [self.get_evidence_document(workspace_id, row["document_id"]) for row in rows]

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
        snapshot = {}
        for table, order_by in (
            ("recovery_events", "event_id"),
            ("exposure_lines", "exposure_id"),
            ("entitlement_bases", "entitlement_id"),
            ("claim_cases", "case_id"),
            ("evidence_documents", "document_id"),
        ):
            snapshot[table] = [
                row["payload"]
                for row in self.conn.execute(
                    f"SELECT payload FROM {table} WHERE workspace_id=? ORDER BY {order_by}",
                    (workspace_id,),
                ).fetchall()
            ]
        return hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
