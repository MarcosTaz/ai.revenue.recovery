from datetime import date

import pytest

from recovery_radar.facts import EvidenceAssertion, resolve_fact


def a(assertion_id, document_id, field, value, *, unit=None, effective_date=None, workspace="A"):
    return EvidenceAssertion(
        assertion_id=assertion_id,
        workspace_id=workspace,
        document_id=document_id,
        subject_key="PRG-1/PART-1",
        field=field,
        value=value,
        unit=unit,
        effective_date=effective_date,
    )


def test_contract_and_po_disagreement_returns_conflicting_not_selected_value():
    result = resolve_fact(
        "A",
        "PRG-1/PART-1",
        "ownership",
        [
            a("A1", "CONTRACT-1", "ownership", "SUPPLIER"),
            a("A2", "PO-1", "ownership", "CUSTOMER"),
        ],
    )
    assert result.state == "CONFLICTING"
    assert result.value is None
    assert result.reason == "DOCUMENTS_DISAGREE_PRECEDENCE_NOT_MODELED"


def test_forecast_and_release_quantity_disagreement_fails_closed():
    result = resolve_fact(
        "A",
        "PRG-1/PART-1",
        "released_quantity",
        [
            a("A1", "FORECAST-1", "released_quantity", "1000", unit="EA", effective_date=date(2026, 7, 1)),
            a("A2", "RELEASE-1", "released_quantity", "650", unit="EA", effective_date=date(2026, 7, 1)),
        ],
    )
    assert result.state == "CONFLICTING"
    assert set(result.document_ids) == {"FORECAST-1", "RELEASE-1"}


def test_same_fact_from_multiple_documents_is_supported_with_lineage():
    result = resolve_fact(
        "A",
        "PRG-1/PART-1",
        "unit_cost",
        [
            a("A1", "COST-1", "unit_cost", "12.50", unit="EUR"),
            a("A2", "LEDGER-1", "unit_cost", "12.50", unit="EUR"),
        ],
    )
    assert result.state == "SUPPORTED"
    assert result.value == "12.50 EUR"
    assert result.assertion_ids == ("A1", "A2")


def test_missing_fact_is_unknown():
    result = resolve_fact("A", "PRG-1/PART-1", "ownership", [])
    assert result.state == "UNKNOWN"
    assert result.value is None


def test_mixed_tenant_assertions_are_rejected():
    with pytest.raises(PermissionError, match="CROSS_TENANT_ASSERTION_SET"):
        resolve_fact(
            "A",
            "PRG-1/PART-1",
            "ownership",
            [a("A1", "DOC-A", "ownership", "SUPPLIER"), a("B1", "DOC-B", "ownership", "SUPPLIER", workspace="B")],
        )
