import json
from pathlib import Path

import pytest

from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.pilot_bundle import (
    BUNDLE_FORMAT,
    PilotBundleError,
    ingest_pilot_bundle,
    load_pilot_bundle,
)
from recovery_radar.storage import Storage


def _write_evidence(root: Path, name: str, content: str) -> str:
    path = root / name
    path.write_text(content, encoding="utf-8")
    return name


def _bundle_payload(root: Path) -> dict:
    files = {
        "notice": _write_evidence(root, "notice.txt", "customer cancellation notice"),
        "inventory": _write_evidence(root, "inventory.csv", "part,qty,cost\nP1,100,10"),
        "contract": _write_evidence(root, "contract.txt", "signed termination clause"),
        "po": _write_evidence(root, "po.txt", "purchase order support"),
        "mitigation": _write_evidence(root, "mitigation.txt", "resale proceeds 200"),
    }
    return {
        "format": BUNDLE_FORMAT,
        "supplier_id": "SUP-A",
        "event": {
            "event_id": "EV-1",
            "customer_id": "OEM-A",
            "program_id": "PRG-A",
            "part_id": "PART-A",
            "event_type": "PROGRAM_CANCELLED",
            "event_date": "2026-07-01",
            "expected_volume": "100",
            "revised_volume": "0",
            "source_ref": "event://1",
            "evidence_ref": "notice://1",
        },
        "exposures": [
            {
                "exposure_id": "EXP-1",
                "event_id": "EV-1",
                "economic_loss_id": "LOSS-1",
                "category": "RAW_MATERIAL",
                "quantity": "100",
                "unit_cost": "10",
                "currency": "EUR",
                "inventory_or_cost_ref": "inventory://1",
                "ownership": "SUPPLIER",
                "mitigation_amount": "200",
                "mitigation_evidence_ref": "mitigation://1",
            }
        ],
        "entitlements": [
            {
                "entitlement_id": "ENT-1",
                "event_id": "EV-1",
                "economic_loss_id": "LOSS-1",
                "support_state": "SUPPORTED",
                "contractual_basis_ref": "contract://1",
                "supporting_document_ref": "po://1",
            }
        ],
        "evidence": [
            {
                "document_id": "D-N",
                "supplier_id": "SUP-A",
                "customer_id": "OEM-A",
                "program_id": "PRG-A",
                "evidence_type": "CUSTOMER_NOTICE",
                "source_ref": "notice://1",
                "version_id": "v1",
                "document_date": "2026-07-01",
                "file": files["notice"],
            },
            {
                "document_id": "D-I",
                "supplier_id": "SUP-A",
                "customer_id": "OEM-A",
                "program_id": "PRG-A",
                "evidence_type": "INVENTORY_RECORD",
                "source_ref": "inventory://1",
                "version_id": "v1",
                "document_date": "2026-07-01",
                "file": files["inventory"],
            },
            {
                "document_id": "D-C",
                "supplier_id": "SUP-A",
                "customer_id": "OEM-A",
                "program_id": "PRG-A",
                "evidence_type": "CONTRACT",
                "source_ref": "contract://1",
                "version_id": "v1",
                "document_date": "2026-01-01",
                "file": files["contract"],
                "signed": True,
            },
            {
                "document_id": "D-P",
                "supplier_id": "SUP-A",
                "customer_id": "OEM-A",
                "program_id": "PRG-A",
                "evidence_type": "PURCHASE_ORDER",
                "source_ref": "po://1",
                "version_id": "v1",
                "document_date": "2026-01-01",
                "file": files["po"],
            },
            {
                "document_id": "D-M",
                "supplier_id": "SUP-A",
                "customer_id": "OEM-A",
                "program_id": "PRG-A",
                "evidence_type": "MITIGATION_RECORD",
                "source_ref": "mitigation://1",
                "version_id": "v1",
                "document_date": "2026-07-02",
                "file": files["mitigation"],
            },
        ],
    }


def _write_bundle(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_bundle_hashes_real_files_and_ingestion_remains_unverified(tmp_path):
    payload = _bundle_payload(tmp_path)
    bundle = load_pilot_bundle(_write_bundle(tmp_path, payload), workspace_id="A")
    assert bundle.supplier_id == "SUP-A"
    assert len(bundle.evidence_documents) == 5
    assert all(len(document.content_sha256) == 64 for document in bundle.evidence_documents)

    store = Storage(tmp_path / "pilot.db")
    try:
        store.create_workspace("A", "Supplier A")
        gateway = RecoveryRadarGateway(store)
        admin = gateway.bootstrap_workspace_admin("A", "owner")
        analyst = gateway.issue_key(admin, "analyst", "ANALYST")
        reviewer = gateway.issue_key(admin, "reviewer", "REVIEWER")
        report = ingest_pilot_bundle(gateway, analyst, bundle)
        assert report["verification_state"] == "REVIEW_REQUIRED"

        before_review = gateway.analyze_event(analyst, "EV-1", "SUP-A")
        assert before_review["claimable_total"] == "0.00"

        for entitlement in bundle.entitlements:
            gateway.review_entitlement_basis(
                reviewer, entitlement.entitlement_id, "VERIFIED", "human checked"
            )
        for document in bundle.evidence_documents:
            gateway.review_evidence_document(
                reviewer, document.document_id, "VERIFIED", "human checked"
            )

        after_review = gateway.analyze_event(analyst, "EV-1", "SUP-A")
        assert after_review["claimable_total"] == "800.00"
    finally:
        store.close()


def test_bundle_rejects_path_escape_before_reading_external_evidence(tmp_path):
    payload = _bundle_payload(tmp_path)
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("must not be read", encoding="utf-8")
    payload["evidence"][0]["file"] = "../outside-secret.txt"
    with pytest.raises(PilotBundleError, match="EVIDENCE_FILE_PATH_ESCAPE"):
        load_pilot_bundle(_write_bundle(tmp_path, payload), workspace_id="A")


def test_bundle_rejects_duplicate_economic_record_ids(tmp_path):
    payload = _bundle_payload(tmp_path)
    payload["exposures"].append(dict(payload["exposures"][0]))
    with pytest.raises(PilotBundleError, match="DUPLICATE_EXPOSURE_ID:EXP-1"):
        load_pilot_bundle(_write_bundle(tmp_path, payload), workspace_id="A")


def test_bundle_rejects_unknown_enum_and_non_finite_decimal(tmp_path):
    payload = _bundle_payload(tmp_path)
    payload["event"]["event_type"] = "MAGIC_EVENT"
    with pytest.raises(PilotBundleError, match="EVENT_TYPE_UNSUPPORTED"):
        load_pilot_bundle(_write_bundle(tmp_path, payload), workspace_id="A")

    payload = _bundle_payload(tmp_path)
    payload["exposures"][0]["quantity"] = "NaN"
    with pytest.raises(PilotBundleError, match="QUANTITY_NON_FINITE"):
        load_pilot_bundle(_write_bundle(tmp_path, payload), workspace_id="A")
