from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional, Tuple

from .engine import FindingState, money


@dataclass(frozen=True)
class SourceTransaction:
    source_system: str
    source_id: str
    amount: Decimal
    contract_id: str
    period: str


@dataclass(frozen=True)
class MigrationLink:
    old_system: str
    old_source_id: str
    new_system: str
    new_source_id: str
    evidence_ids: Tuple[str, ...]

    def __post_init__(self):
        if not self.evidence_ids:
            raise ValueError("Migration link requires evidence")


def trace_migrated_transaction(
    old: SourceTransaction,
    new: Optional[SourceTransaction],
    links: Iterable[MigrationLink],
):
    if new is None:
        return {
            "state": FindingState.UNKNOWN,
            "amount": None,
            "explanation": "No successor transaction is available after system migration.",
        }

    matching = [
        link for link in links
        if link.old_system == old.source_system
        and link.old_source_id == old.source_id
        and link.new_system == new.source_system
        and link.new_source_id == new.source_id
    ]
    if len(matching) != 1:
        return {
            "state": FindingState.UNKNOWN,
            "amount": None,
            "explanation": "Migration lineage is missing or ambiguous.",
        }
    if old.contract_id != new.contract_id or old.period != new.period:
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "amount": None,
            "explanation": "Migrated transaction changed contract or period classification.",
        }
    if money(old.amount) != money(new.amount):
        return {
            "state": FindingState.REQUIRES_REVIEW,
            "amount": None,
            "explanation": "Migrated transaction amount changed and requires reconciliation.",
        }
    return {
        "state": FindingState.NO_VARIANCE,
        "amount": money(new.amount),
        "explanation": "Transaction lineage is supported across accounting systems.",
    }
