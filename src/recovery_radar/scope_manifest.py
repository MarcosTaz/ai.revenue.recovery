from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .pilot_bundle import PilotBundle

FORMAT = "RECOVERY_RADAR_SOURCE_SCOPE_V1"


def build_source_scope_manifest(bundle: PilotBundle) -> dict:
    """Describe the normalized pilot source set without embedding raw evidence bytes."""
    payload = {
        "format": FORMAT,
        "supplier_id": bundle.supplier_id,
        "event": {
            "event_id": bundle.event.event_id,
            "customer_id": bundle.event.customer_id,
            "program_id": bundle.event.program_id,
            "part_id": bundle.event.part_id,
            "event_type": bundle.event.event_type,
            "event_date": bundle.event.event_date.isoformat(),
            "source_ref": bundle.event.source_ref,
            "evidence_ref": bundle.event.evidence_ref,
        },
        "exposures": [
            {
                "exposure_id": line.exposure_id,
                "economic_loss_id": line.economic_loss_id,
                "category": line.category,
                "currency": line.currency,
                "inventory_or_cost_ref": line.inventory_or_cost_ref,
                "mitigation_evidence_ref": line.mitigation_evidence_ref,
                "reimbursement_evidence_ref": line.reimbursement_evidence_ref,
            }
            for line in sorted(bundle.exposures, key=lambda item: item.exposure_id)
        ],
        "entitlements": [
            {
                "entitlement_id": basis.entitlement_id,
                "economic_loss_id": basis.economic_loss_id,
                "contractual_basis_ref": basis.contractual_basis_ref,
                "supporting_document_ref": basis.supporting_document_ref,
            }
            for basis in sorted(bundle.entitlements, key=lambda item: item.entitlement_id)
        ],
        "evidence": [
            {
                "document_id": document.document_id,
                "evidence_type": document.evidence_type,
                "source_ref": document.source_ref,
                "version_id": document.version_id,
                "document_date": (
                    document.document_date.isoformat() if document.document_date else None
                ),
                "content_sha256": document.content_sha256,
            }
            for document in sorted(
                bundle.evidence_documents, key=lambda item: item.document_id
            )
        ],
        "raw_evidence_bytes_embedded": False,
        "authorization_status": "NOT_INFERRED_FROM_SOURCE_SCOPE",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    payload["source_scope_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def canonical_source_scope_bytes(manifest: dict) -> bytes:
    return (
        json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def export_source_scope_atomic(manifest: dict, destination: str | Path) -> dict:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = canonical_source_scope_bytes(manifest)
    expected = hashlib.sha256(content).hexdigest()
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        persisted = destination.read_bytes()
        actual = hashlib.sha256(persisted).hexdigest()
        if persisted != content or actual != expected:
            destination.unlink(missing_ok=True)
            raise RuntimeError("SOURCE_SCOPE_EXPORT_VERIFICATION_FAILED")
        return {
            "format": FORMAT,
            "source_scope_sha256": manifest["source_scope_sha256"],
            "artifact_sha256": actual,
            "byte_length": len(persisted),
            "path": str(destination),
        }
    except Exception:
        temporary.unlink(missing_ok=True)
        raise