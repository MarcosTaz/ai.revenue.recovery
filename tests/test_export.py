import json
from datetime import date

import pytest

from recovery_radar.engine import analyze_claim
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.export import (
    EXPORT_FORMAT,
    canonical_claim_package_bytes,
    claim_package_export_manifest,
    export_claim_package_atomic,
    verify_claim_package_export,
)
from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.package import build_claim_package
from recovery_radar.storage import Storage
from recovery_radar.synthetic import alpha_components_fixture


def _document(document_id, source_ref, evidence_type, *, signed=None):
    return EvidenceDocument.from_bytes(
        document_id=document_id,
        workspace_id="A",
        supplier_id="SUP-A",
        customer_id="OEM-A",
        program_id="PRG-A",
        evidence_type=evidence_type,
        source_ref=source_ref,
        version_id="v1",
        document_date=date(2026, 1, 1),
        content=f"{document_id}:{source_ref}".encode(),
        signed=signed,
    )


def _seed_verified(gateway, analyst, reviewer):
    event, exposures, entitlements, _ = alpha_components_fixture()
    gateway.store_recovery_event(analyst, event)
    for exposure in exposures:
        gateway.store_exposure_line(analyst, exposure)
    for entitlement in entitlements:
        gateway.store_entitlement_basis(analyst, entitlement)
        gateway.review_entitlement_basis(reviewer, entitlement.entitlement_id, "VERIFIED")
    documents = (
        _document("D-N", "document://alpha/customer-notice", "CUSTOMER_NOTICE"),
        _document("D-I", "inventory://alpha/A1", "INVENTORY_RECORD"),
        _document("D-C", "contract://alpha/termination-clause", "CONTRACT", signed=True),
        _document("D-P", "po://alpha/PO-1", "PURCHASE_ORDER"),
        _document("D-M", "mitigation://alpha/resale", "MITIGATION_RECORD"),
    )
    for document in documents:
        gateway.store_evidence_document(analyst, document)
        gateway.review_evidence_document(reviewer, document.document_id, "VERIFIED")
    return event


def test_canonical_export_is_deterministic_and_self_describing():
    event, exposures, entitlements, _ = alpha_components_fixture()
    package = build_claim_package(analyze_claim(event, exposures, entitlements))
    first = canonical_claim_package_bytes(package)
    second = canonical_claim_package_bytes(package)
    assert first == second
    decoded = json.loads(first)
    assert decoded["format"] == EXPORT_FORMAT
    assert decoded["package"] == package
    manifest = claim_package_export_manifest(package)
    assert manifest["format"] == EXPORT_FORMAT
    assert manifest["byte_length"] == len(first)
    assert len(manifest["sha256"]) == 64


def test_atomic_export_round_trip_and_tamper_detection(tmp_path):
    event, exposures, entitlements, _ = alpha_components_fixture()
    package = build_claim_package(analyze_claim(event, exposures, entitlements))
    destination = tmp_path / "claim-package.json"
    manifest = export_claim_package_atomic(package, destination)
    verified = verify_claim_package_export(destination, manifest["sha256"])
    assert verified["package"] == package
    destination.write_text('{"tampered":true}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="CLAIM_PACKAGE_EXPORT_HASH_MISMATCH"):
        verify_claim_package_export(destination, manifest["sha256"])


def test_authenticated_gateway_exports_current_tenant_package(tmp_path):
    store = Storage(tmp_path / "export.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "admin")
        analyst = gateway.issue_key(admin, "analyst", "ANALYST")
        reviewer = gateway.issue_key(admin, "reviewer", "REVIEWER")
        event = _seed_verified(gateway, analyst, reviewer)
        destination = tmp_path / "delivery.json"
        manifest = gateway.export_claim_package(
            analyst, event.event_id, "SUP-A", destination
        )
        verified = verify_claim_package_export(destination, manifest["sha256"])
        package = verified["package"]
        assert package["workspace_id"] == "A"
        assert package["executive_summary"]["claimable_total"] == "800.00"
        assert package["audit_trail"]
        assert manifest["path"] == str(destination)
    finally:
        store.close()


def test_invalid_token_cannot_create_export_file(tmp_path):
    store = Storage(tmp_path / "export.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        gateway.bootstrap_workspace_admin("A", "admin")
        destination = tmp_path / "must-not-exist.json"
        with pytest.raises(PermissionError, match="INVALID_API_KEY"):
            gateway.export_claim_package(
                "rrk_invalid.invalid", "EV-X", "SUP-A", destination
            )
        assert not destination.exists()
    finally:
        store.close()
