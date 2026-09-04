from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Tuple

from .engine import FindingState, RateState, money


@dataclass(frozen=True)
class IndirectLayer:
    pool_id: str
    allocation_base: Decimal
    rate: Decimal
    rate_state: RateState
    pool_supported: bool
    base_supported: bool
    depends_on: Tuple[str, ...] = ()


def compute_multi_pool(layers: Iterable[IndirectLayer]):
    items = list(layers)
    if len({item.pool_id for item in items}) != len(items):
        raise ValueError("Duplicate indirect pool id")
    ids = {item.pool_id for item in items}
    for item in items:
        if any(dep not in ids for dep in item.depends_on):
            return {"state": FindingState.UNKNOWN, "total": None, "layers": {}}
        if item.rate_state != RateState.SETTLED_FINAL:
            return {"state": FindingState.REQUIRES_REVIEW, "total": None, "layers": {}}
        if not item.pool_supported or not item.base_supported:
            return {"state": FindingState.REQUIRES_REVIEW, "total": None, "layers": {}}
        if item.allocation_base < 0 or item.rate < 0:
            raise ValueError("Indirect base and rate must be non-negative")

    visiting: set[str] = set()
    visited: set[str] = set()
    graph = {item.pool_id: item.depends_on for item in items}

    def visit(pool_id: str):
        if pool_id in visiting:
            raise ValueError("Indirect allocation dependency cycle")
        if pool_id in visited:
            return
        visiting.add(pool_id)
        for dep in graph[pool_id]:
            visit(dep)
        visiting.remove(pool_id)
        visited.add(pool_id)

    for pool_id in graph:
        visit(pool_id)

    amounts = {item.pool_id: money(item.allocation_base * item.rate) for item in items}
    total = money(sum(amounts.values(), Decimal("0")))
    return {"state": FindingState.NO_VARIANCE, "total": total, "layers": amounts}
