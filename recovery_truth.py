from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence

from aviation_recovery import EvaluationResult, Status


MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def summarize_recovery_truth(results: Sequence[EvaluationResult]) -> dict[str, object]:
    currencies = {result.currency for result in results if result.currency != "UNKNOWN"}
    if len(currencies) > 1:
        raise ValueError("recovery truth summary requires one currency or prior FX normalization")

    claim_ready = [result for result in results if result.status == Status.CLAIM_READY]
    review_required = [result for result in results if result.status == Status.REVIEW_REQUIRED]
    blocked = [result for result in results if result.status == Status.BLOCKED]
    zero = [result for result in results if result.status == Status.ZERO_ENTITLEMENT]

    verified_ready = sum((r.net_recoverable for r in claim_ready), Decimal("0"))
    review_pipeline = sum((r.net_recoverable for r in review_required), Decimal("0"))
    blocked_potential = sum((r.net_recoverable for r in blocked), Decimal("0"))

    return {
        "currency": next(iter(currencies), "UNKNOWN"),
        "candidate_count": len(results),
        "claim_ready_count": len(claim_ready),
        "review_required_count": len(review_required),
        "blocked_count": len(blocked),
        "zero_entitlement_count": len(zero),
        "verified_claim_ready_recovery": _money(verified_ready),
        "review_required_pipeline": _money(review_pipeline),
        "blocked_potential": _money(blocked_potential),
        "total_identified_before_status_filter": _money(
            verified_ready + review_pipeline + blocked_potential
        ),
    }
