from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .domain import EconomicFinding
from .engine import FindingState, money


@dataclass(frozen=True)
class EconomicSummary:
    recovery_candidates: Decimal
    payable_candidates: Decimal
    no_variance_count: int
    review_count: int
    unknown_count: int
    finding_count: int


def summarize_findings(findings: Iterable[EconomicFinding]) -> EconomicSummary:
    recovery = Decimal("0")
    payable = Decimal("0")
    no_variance = 0
    review = 0
    unknown = 0
    count = 0

    for finding in findings:
        count += 1
        if finding.state == FindingState.RECOVERY_CANDIDATE:
            if finding.variance is None or finding.variance <= 0:
                raise ValueError("Recovery candidate must have positive variance")
            recovery += finding.variance
        elif finding.state == FindingState.PAYABLE_CANDIDATE:
            if finding.variance is None or finding.variance >= 0:
                raise ValueError("Payable candidate must have negative variance")
            payable += abs(finding.variance)
        elif finding.state == FindingState.NO_VARIANCE:
            no_variance += 1
        elif finding.state == FindingState.REQUIRES_REVIEW:
            review += 1
        elif finding.state == FindingState.UNKNOWN:
            unknown += 1

    return EconomicSummary(
        recovery_candidates=money(recovery),
        payable_candidates=money(payable),
        no_variance_count=no_variance,
        review_count=review,
        unknown_count=unknown,
        finding_count=count,
    )
