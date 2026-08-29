from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Literal

FactState = Literal["SUPPORTED", "CONFLICTING", "UNKNOWN"]


@dataclass(frozen=True, slots=True)
class EvidenceAssertion:
    assertion_id: str
    workspace_id: str
    document_id: str
    subject_key: str
    field: str
    value: str
    unit: str | None = None
    effective_date: date | None = None


@dataclass(frozen=True, slots=True)
class FactResolution:
    state: FactState
    subject_key: str
    field: str
    value: str | None
    assertion_ids: tuple[str, ...]
    document_ids: tuple[str, ...]
    reason: str


def resolve_fact(
    workspace_id: str,
    subject_key: str,
    field: str,
    assertions: Iterable[EvidenceAssertion],
) -> FactResolution:
    relevant = [
        item
        for item in assertions
        if item.subject_key == subject_key and item.field == field
    ]
    if any(item.workspace_id != workspace_id for item in relevant):
        raise PermissionError("CROSS_TENANT_ASSERTION_SET")
    if not relevant:
        return FactResolution(
            "UNKNOWN", subject_key, field, None, (), (), "NO_DOCUMENTARY_ASSERTION"
        )

    identities = {(item.value, item.unit, item.effective_date) for item in relevant}
    assertion_ids = tuple(sorted(item.assertion_id for item in relevant))
    document_ids = tuple(sorted({item.document_id for item in relevant}))
    if len(identities) != 1:
        return FactResolution(
            "CONFLICTING",
            subject_key,
            field,
            None,
            assertion_ids,
            document_ids,
            "DOCUMENTS_DISAGREE_PRECEDENCE_NOT_MODELED",
        )

    value, unit, effective_date = next(iter(identities))
    rendered = value
    if unit:
        rendered = f"{rendered} {unit}"
    if effective_date:
        rendered = f"{rendered} @ {effective_date.isoformat()}"
    return FactResolution(
        "SUPPORTED",
        subject_key,
        field,
        rendered,
        assertion_ids,
        document_ids,
        "UNANIMOUS_DOCUMENTARY_ASSERTIONS",
    )
