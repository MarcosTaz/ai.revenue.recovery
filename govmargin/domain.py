from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import FrozenSet, Optional, Tuple

from .engine import FindingState


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source_type: str
    source_locator: str
    sha256: str
    observed_at: datetime

    def __post_init__(self):
        if len(self.sha256) != 64:
            raise ValueError("EvidenceRef.sha256 must be a 64-character SHA-256 hex digest")
        int(self.sha256, 16)


@dataclass(frozen=True)
class ContractVersion:
    contract_id: str
    version_id: str
    effective_date: date
    clauses: FrozenSet[str]
    modification_ids: Tuple[str, ...] = ()
    supersedes_version_id: Optional[str] = None


@dataclass(frozen=True)
class RateAgreement:
    agreement_id: str
    contractor_id: str
    fiscal_year: int
    settled: bool
    settled_date: Optional[date]
    evidence_ids: Tuple[str, ...]

    def __post_init__(self):
        if self.settled and self.settled_date is None:
            raise ValueError("Settled rate agreement requires settled_date")
        if not self.evidence_ids:
            raise ValueError("Rate agreement requires evidence lineage")


@dataclass(frozen=True)
class EconomicFinding:
    finding_id: str
    contract_id: str
    state: FindingState
    expected_amount: Optional[Decimal]
    billed_amount: Optional[Decimal]
    paid_amount: Optional[Decimal]
    variance: Optional[Decimal]
    evidence_ids: Tuple[str, ...]
    rule_ids: Tuple[str, ...]
    assumptions: Tuple[str, ...] = ()
    human_reviewed: bool = False

    def __post_init__(self):
        if self.state in {FindingState.RECOVERY_CANDIDATE, FindingState.PAYABLE_CANDIDATE}:
            if self.variance is None:
                raise ValueError("Candidate finding requires deterministic variance")
            if not self.evidence_ids:
                raise ValueError("Candidate finding requires evidence lineage")
            if not self.rule_ids:
                raise ValueError("Candidate finding requires rule lineage")


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    occurred_at: datetime
    actor: str
    action: str
    subject_id: str
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
