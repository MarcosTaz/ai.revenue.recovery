from datetime import date
from decimal import Decimal

import pytest

from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.models import EntitlementBasis, ExposureLine, RecoveryEvent
from recovery_radar.pilot_bundle import BUNDLE_FORMAT, PilotBundle, ingest_pilot_bundle
from recovery_radar.storage import Storage


def _event():
    return RecoveryEvent(
        "EV-BUNDLE",
        "OEM-A",
        "PRG-A",
        "PART-A",
        "PROGRAM_CANCELLED",
        date(2026, 7, 1),
        Decimal("100"),
        Decimal("0"),
        "event://bundle",
        "notice://bundle",
    )


def _line(exposure_id, loss_id, quantity="10"):
    return ExposureLine(
        exposure_id,
        "EV-BUNDLE",
        loss_id,
        "RAW_MATERIAL",
        Decimal(quantity),
        Decimal("10"),
        "EUR",
        f"inventory://{exposure_id}",
        "SUPPLIER",
    )


def _basis(entitlement_id, loss_id):
    return EntitlementBasis(
        entitlement_id,
        "EV-BUNDLE",
        loss_id,
        "SUPPORTED",
        f"contract://{entitlement_id}",
        f"po://{entitlement_id}",
    )


def _bundle(exposures, entitlements=()):
    return PilotBundle(
        BUNDLE_FORMAT,
        "SUP-A",
        _event(),
        tuple(exposures),
        tuple(entitlements),
        (),
    )


def _gateway(tmp_path):
    store = Storage(tmp_path / "bundle.db")
    store.create_workspace("A", "Supplier A")
    gateway = RecoveryRadarGateway(store)
    admin = gateway.bootstrap_workspace_admin("A", "owner")
    analyst = gateway.issue_key(admin, "analyst", "ANALYST")
    return store, gateway, analyst


def test_conflict_mid_bundle_rolls_back_every_new_row_and_audit(tmp_path):
    store, gateway, analyst = _gateway(tmp_path)
    try:
        gateway.store_recovery_event(analyst, _event())
        existing = _line("EXP-CONFLICT", "LOSS-CONFLICT", "1")
        gateway.store_exposure_line(analyst, existing)
        audit_before = store.audit_count("A")

        incoming = _bundle(
            [
                _line("EXP-NEW", "LOSS-NEW", "5"),
                _line("EXP-CONFLICT", "LOSS-CONFLICT", "99"),
            ]
        )
        with pytest.raises(ValueError, match="EXPOSURE_LINE_ID_CONFLICT"):
            ingest_pilot_bundle(gateway, analyst, incoming)

        assert gateway.tenant.get_exposure_line(
            gateway.auth.authenticate(analyst), "EXP-NEW"
        ) is None
        recovered = gateway.tenant.get_exposure_line(
            gateway.auth.authenticate(analyst), "EXP-CONFLICT"
        )
        assert recovered.quantity == Decimal("1")
        assert store.audit_count("A") == audit_before
    finally:
        store.close()


def test_exact_bundle_retry_is_idempotent_and_does_not_duplicate_audit(tmp_path):
    store, gateway, analyst = _gateway(tmp_path)
    try:
        bundle = _bundle(
            [_line("EXP-1", "LOSS-1")],
            [_basis("ENT-1", "LOSS-1")],
        )
        first = ingest_pilot_bundle(gateway, analyst, bundle)
        audit_after_first = store.audit_count("A")
        second = ingest_pilot_bundle(gateway, analyst, bundle)

        assert first["created"] == {
            "event": 1,
            "exposures": 1,
            "entitlements": 1,
            "evidence_documents": 0,
        }
        assert second["created"] == {
            "event": 0,
            "exposures": 0,
            "entitlements": 0,
            "evidence_documents": 0,
        }
        assert first["transaction_state"] == "COMMITTED_ATOMICALLY"
        assert second["transaction_state"] == "COMMITTED_ATOMICALLY"
        assert store.audit_count("A") == audit_after_first
    finally:
        store.close()


def test_interrupted_audit_inside_bundle_rolls_back_source_truth(tmp_path, monkeypatch):
    store, gateway, analyst = _gateway(tmp_path)
    try:
        original_audit = store._audit
        calls = {"count": 0}

        def fail_second_audit(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("SIMULATED_BUNDLE_AUDIT_FAILURE")
            return original_audit(*args, **kwargs)

        monkeypatch.setattr(store, "_audit", fail_second_audit)
        bundle = _bundle([_line("EXP-1", "LOSS-1")])
        with pytest.raises(RuntimeError, match="SIMULATED_BUNDLE_AUDIT_FAILURE"):
            ingest_pilot_bundle(gateway, analyst, bundle)

        assert gateway.tenant.get_recovery_event(
            gateway.auth.authenticate(analyst), "EV-BUNDLE"
        ) is None
        assert gateway.tenant.get_exposure_line(
            gateway.auth.authenticate(analyst), "EXP-1"
        ) is None
        assert store.audit_count("A") == 0
    finally:
        store.close()
