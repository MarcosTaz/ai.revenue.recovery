from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generic, Iterable, Mapping, Tuple, TypeVar


T = TypeVar("T")


class TenantStorageError(ValueError):
    pass


@dataclass(frozen=True)
class TenantRecord(Generic[T]):
    organization_id: str
    record_id: str
    value: T

    def __post_init__(self):
        if not self.organization_id.strip() or not self.record_id.strip():
            raise TenantStorageError("organization_id and record_id are required")


class ImmutableTenantStore(Generic[T]):
    """In-memory reference implementation of tenant/immutability invariants.

    This is not production persistence and provides no encryption or durability.
    It exists so application code can be tested against a fail-closed storage
    contract before a production datastore is connected.
    """

    def __init__(self) -> None:
        self._records: Dict[tuple[str, str], TenantRecord[T]] = {}

    def put_once(self, record: TenantRecord[T]) -> None:
        key = (record.organization_id, record.record_id)
        if key in self._records:
            raise TenantStorageError("immutable record already exists")
        self._records[key] = record

    def get(self, organization_id: str, record_id: str) -> TenantRecord[T]:
        if not organization_id.strip() or not record_id.strip():
            raise TenantStorageError("organization_id and record_id are required")
        key = (organization_id, record_id)
        if key not in self._records:
            raise KeyError(record_id)
        return self._records[key]

    def list_for_organization(self, organization_id: str) -> Tuple[TenantRecord[T], ...]:
        if not organization_id.strip():
            raise TenantStorageError("organization_id is required")
        return tuple(
            record
            for (record_org, _), record in self._records.items()
            if record_org == organization_id
        )

    def count(self) -> int:
        return len(self._records)
