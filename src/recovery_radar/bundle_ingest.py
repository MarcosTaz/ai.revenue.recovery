from __future__ import annotations

import json
from typing import Any


def _raw(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def _insert_immutable_tx(
    storage,
    *,
    table: str,
    workspace_id: str,
    id_column: str,
    entity_id: str,
    payload: dict[str, Any],
    actor_id: str,
    entity_type: str,
    extra_columns: tuple[str, ...] = (),
    extra_values: tuple[str, ...] = (),
) -> bool:
    raw = _raw(payload)
    existing = storage.conn.execute(
        f"SELECT payload FROM {table} WHERE workspace_id=? AND {id_column}=?",
        (workspace_id, entity_id),
    ).fetchone()
    if existing is not None:
        if existing["payload"] == raw:
            return False
        raise ValueError(f"{entity_type}_ID_CONFLICT")
    columns = ("workspace_id", id_column, *extra_columns, "payload")
    placeholders = ",".join("?" for _ in columns)
    storage.conn.execute(
        f"INSERT INTO {table}({','.join(columns)}) VALUES ({placeholders})",
        (workspace_id, entity_id, *extra_values, raw),
    )
    storage._audit(
        workspace_id, actor_id, entity_type, entity_id, "CREATE", payload
    )
    return True


def ingest_bundle_atomic(gateway, token: str, bundle) -> dict[str, Any]:
    """Persist one pilot bundle as one SQLite transaction.

    Authentication and role are derived from the token. Existing identical rows
    make retries idempotent. Any conflicting or interrupted write rolls back the
    entire bundle transaction, including its audit events.
    """
    principal = gateway.auth.authenticate(token)
    if principal.role not in {"ADMIN", "ANALYST"}:
        raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_SOURCE_WRITE")
    storage = gateway.tenant.storage
    workspace_id = principal.workspace_id
    storage._workspace_exists(workspace_id)

    if any(
        document.workspace_id != workspace_id
        for document in bundle.evidence_documents
    ):
        raise PermissionError("CROSS_TENANT_DOCUMENT_REJECTED")
    if any(line.event_id != bundle.event.event_id for line in bundle.exposures):
        raise ValueError("BUNDLE_EXPOSURE_EVENT_MISMATCH")
    if any(basis.event_id != bundle.event.event_id for basis in bundle.entitlements):
        raise ValueError("BUNDLE_ENTITLEMENT_EVENT_MISMATCH")

    created = {
        "event": 0,
        "exposures": 0,
        "entitlements": 0,
        "evidence_documents": 0,
    }
    storage.conn.execute("BEGIN IMMEDIATE")
    try:
        if _insert_immutable_tx(
            storage,
            table="recovery_events",
            workspace_id=workspace_id,
            id_column="event_id",
            entity_id=bundle.event.event_id,
            payload=storage._serialize_event(bundle.event),
            actor_id=principal.actor_id,
            entity_type="RECOVERY_EVENT",
        ):
            created["event"] += 1

        for line in bundle.exposures:
            if _insert_immutable_tx(
                storage,
                table="exposure_lines",
                workspace_id=workspace_id,
                id_column="exposure_id",
                entity_id=line.exposure_id,
                payload=storage._serialize_exposure(line),
                actor_id=principal.actor_id,
                entity_type="EXPOSURE_LINE",
                extra_columns=("event_id",),
                extra_values=(line.event_id,),
            ):
                created["exposures"] += 1

        for basis in bundle.entitlements:
            if _insert_immutable_tx(
                storage,
                table="entitlement_bases",
                workspace_id=workspace_id,
                id_column="entitlement_id",
                entity_id=basis.entitlement_id,
                payload=storage._serialize_entitlement(basis),
                actor_id=principal.actor_id,
                entity_type="ENTITLEMENT_BASIS",
                extra_columns=("event_id", "economic_loss_id"),
                extra_values=(basis.event_id, basis.economic_loss_id),
            ):
                created["entitlements"] += 1

        for document in bundle.evidence_documents:
            payload = storage._serialize_document(document)
            raw = _raw(payload)
            existing = storage.conn.execute(
                "SELECT payload FROM evidence_documents WHERE workspace_id=? AND document_id=?",
                (workspace_id, document.document_id),
            ).fetchone()
            if existing is not None:
                if existing["payload"] == raw:
                    continue
                raise ValueError("DOCUMENT_ID_VERSION_CONFLICT")
            duplicate = storage.conn.execute(
                "SELECT document_id FROM evidence_documents WHERE workspace_id=? AND content_sha256=?",
                (workspace_id, document.content_sha256),
            ).fetchone()
            if duplicate is not None:
                raise ValueError(
                    f"DUPLICATE_DOCUMENT_CONTENT:{duplicate['document_id']}"
                )
            storage.conn.execute(
                "INSERT INTO evidence_documents(workspace_id,document_id,content_sha256,payload) VALUES (?,?,?,?)",
                (
                    workspace_id,
                    document.document_id,
                    document.content_sha256,
                    raw,
                ),
            )
            storage._audit(
                workspace_id,
                principal.actor_id,
                "EVIDENCE_DOCUMENT",
                document.document_id,
                "CREATE",
                payload,
            )
            created["evidence_documents"] += 1

        storage.conn.commit()
    except Exception:
        storage.conn.rollback()
        raise

    return {
        "format": bundle.format,
        "supplier_id": bundle.supplier_id,
        "event_id": bundle.event.event_id,
        "exposure_count": len(bundle.exposures),
        "entitlement_count": len(bundle.entitlements),
        "evidence_document_count": len(bundle.evidence_documents),
        "created": created,
        "verification_state": "REVIEW_REQUIRED",
        "transaction_state": "COMMITTED_ATOMICALLY",
    }
