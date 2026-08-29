import hashlib
import json
from datetime import date
from decimal import Decimal

from recovery_radar.evidence import EvidenceDocument
from recovery_radar.models import EntitlementBasis, ExposureLine, RecoveryEvent
from recovery_radar.pilot_bundle import BUNDLE_FORMAT, PilotBundle
from recovery_radar.scope_manifest import (
    FORMAT,
    build_source_scope_manifest,
    export_source_scope_atomic,
)


def _bundle(evidence_bytes=b"contract evidence", *, quantity="10", unit_cost="12.50"):
    event = RecoveryEvent(
        "EV-1", "OEM-A", "PRG-A", "PART-A", "PROGRAM_CANCELLED",
        date(2026, 7, 1), Decimal("100"), Decimal("0"),
        "event://1", "notice://1",
    )
    exposure = ExposureLine(
        "EXP-1", "EV-1", "LOSS-1", "RAW_MATERIAL", Decimal(quantity),
        Decimal(unit_cost), "EUR", "inventory://1", "SUPPLIER",
    )
    entitlement = EntitlementBasis(
        "ENT-1", "EV-1", "LOSS-1", "SUPPORTED", "contract://1", "po://1"
    )
    evidence = EvidenceDocument.from_bytes(
        document_id="DOC-1",
        workspace_id="A",
        supplier_id="SUP-A",
        customer_id="OEM-A",
        program_id="PRG-A",
        evidence_type="CONTRACT",
        source_ref="contract://1",
        version_id="v1",
        document_date=date(2026, 1, 1),
        content=evidence_bytes,
        signed=True,
    )
    return PilotBundle(
        BUNDLE_FORMAT, "SUP-A", event, (exposure,), (entitlement,), (evidence,)
    )


def test_source_scope_is_deterministic_and_contains_no_raw_evidence_bytes():
    first = build_source_scope_manifest(_bundle())
    second = build_source_scope_manifest(_bundle())
    assert first == second
    assert first["format"] == FORMAT
    assert len(first["source_scope_sha256"]) == 64
    assert first["raw_evidence_bytes_embedded"] is False
    serialized = json.dumps(first)
    assert "contract evidence" not in serialized
    assert first["evidence"][0]["content_sha256"] == hashlib.sha256(b"contract evidence").hexdigest()
    assert first["authorization_status"] == "NOT_INFERRED_FROM_SOURCE_SCOPE"


def test_source_scope_hash_changes_when_evidence_bytes_change():
    first = build_source_scope_manifest(_bundle(b"version one"))
    second = build_source_scope_manifest(_bundle(b"version two"))
    assert first["source_scope_sha256"] != second["source_scope_sha256"]


def test_source_scope_hash_changes_when_economic_truth_changes():
    baseline = build_source_scope_manifest(_bundle(quantity="10", unit_cost="12.50"))
    changed_quantity = build_source_scope_manifest(_bundle(quantity="11", unit_cost="12.50"))
    changed_cost = build_source_scope_manifest(_bundle(quantity="10", unit_cost="12.51"))
    assert baseline["source_scope_sha256"] != changed_quantity["source_scope_sha256"]
    assert baseline["source_scope_sha256"] != changed_cost["source_scope_sha256"]


def test_source_scope_export_is_atomic_and_manifest_bound(tmp_path):
    manifest = build_source_scope_manifest(_bundle())
    destination = tmp_path / "scope" / "source-scope.json"
    first = export_source_scope_atomic(manifest, destination)
    first_bytes = destination.read_bytes()
    second = export_source_scope_atomic(manifest, destination)
    assert destination.read_bytes() == first_bytes
    assert first["source_scope_sha256"] == manifest["source_scope_sha256"]
    assert second["artifact_sha256"] == hashlib.sha256(first_bytes).hexdigest()
    envelope = json.loads(first_bytes.decode("utf-8"))
    assert envelope["source_scope_sha256"] == manifest["source_scope_sha256"]