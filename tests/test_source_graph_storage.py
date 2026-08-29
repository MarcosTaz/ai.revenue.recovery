from datetime import date
from decimal import Decimal

import pytest

from recovery_radar.auth import Principal
from recovery_radar.models import EntitlementBasis, ExposureLine, RecoveryEvent
from recovery_radar.service import TenantService
from recovery_radar.storage import Storage


def principal(workspace="A", role="ANALYST"):
    return Principal(workspace, f"actor-{workspace}", role)


def event(**overrides):
    values = dict(
        event_id="EV-1",
        customer_id="OEM-1",
        program_id="PRG-1",
        part_id="PART-1",
        event_type="PROGRAM_CANCELLED",
        event_date=date(2026, 7, 1),
        expected_volume=Decimal("1000"),
        revised_volume=Decimal("0"),
        source_ref="event://EV-1",
        evidence_ref="document://notice-1",
    )
    values.update(overrides)
    return RecoveryEvent(**values)


def exposure(**overrides):
    values = dict(
        exposure_id="EXP-1",
        event_id="EV-1",
        economic_loss_id="LOSS-1",
        category="RAW_MATERIAL",
        quantity=Decimal("10"),
        unit_cost=Decimal("12.50"),
        currency="EUR",
        inventory_or_cost_ref="inventory://1",
        ownership="SUPPLIER",
    )
    values.update(overrides)
    return ExposureLine(**values)


def entitlement(**overrides):
    values = dict(
        entitlement_id="ENT-1",
        event_id="EV-1",
        economic_loss_id="LOSS-1",
        support_state="SUPPORTED",
        contractual_basis_ref="contract://1",
        supporting_document_ref="po://1",
    )
    values.update(overrides)
    return EntitlementBasis(**values)


def test_source_graph_round_trips_with_exact_economic_values(tmp_path):
    store = Storage(tmp_path / "graph.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        p = principal()
        service.store_recovery_event(p, event())
        service.store_exposure_line(p, exposure())
        service.store_entitlement_basis(p, entitlement())
        assert service.get_recovery_event(p, "EV-1").expected_volume == Decimal("1000")
        assert service.get_exposure_line(p, "EXP-1").unit_cost == Decimal("12.50")
        assert service.get_entitlement_basis(p, "ENT-1").support_state == "SUPPORTED"
    finally:
        store.close()


def test_child_record_cannot_reference_event_existing_only_in_other_tenant(tmp_path):
    store = Storage(tmp_path / "graph.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        service.store_recovery_event(principal("B"), event())
        with pytest.raises(KeyError, match="PARENT_EVENT_NOT_FOUND"):
            service.store_exposure_line(principal("A"), exposure())
        with pytest.raises(KeyError, match="PARENT_EVENT_NOT_FOUND"):
            service.store_entitlement_basis(principal("A"), entitlement())
    finally:
        store.close()


def test_same_event_id_isolated_between_tenants(tmp_path):
    store = Storage(tmp_path / "graph.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        service.store_recovery_event(principal("A"), event(customer_id="OEM-A"))
        service.store_recovery_event(principal("B"), event(customer_id="OEM-B"))
        assert service.get_recovery_event(principal("A"), "EV-1").customer_id == "OEM-A"
        assert service.get_recovery_event(principal("B"), "EV-1").customer_id == "OEM-B"
    finally:
        store.close()


def test_source_record_id_cannot_silently_change_economic_truth(tmp_path):
    store = Storage(tmp_path / "graph.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        p = principal()
        service.store_recovery_event(p, event(expected_volume=Decimal("1000")))
        with pytest.raises(ValueError, match="RECOVERY_EVENT_ID_CONFLICT"):
            service.store_recovery_event(p, event(expected_volume=Decimal("500")))
    finally:
        store.close()


def test_reviewer_cannot_write_source_economics(tmp_path):
    store = Storage(tmp_path / "graph.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        with pytest.raises(PermissionError, match="SOURCE_WRITE"):
            service.store_recovery_event(principal(role="REVIEWER"), event())
    finally:
        store.close()


def test_backup_digest_includes_event_exposure_entitlement_graph(tmp_path):
    original = tmp_path / "original.db"
    backup = tmp_path / "backup.db"
    store = Storage(original)
    store.create_workspace("A", "Supplier A")
    service = TenantService(store)
    p = principal()
    service.store_recovery_event(p, event())
    service.store_exposure_line(p, exposure())
    service.store_entitlement_basis(p, entitlement())
    before = store.economic_digest("A")
    store.backup_to(backup)
    store.close()
    restored = Storage(backup)
    try:
        assert restored.economic_digest("A") == before
        assert restored.get_exposure_line("A", "EXP-1").economic_loss_id == "LOSS-1"
    finally:
        restored.close()
