from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional, Tuple

from .engine import FindingState, money


@dataclass(frozen=True)
class ContractEconomicState:
    effective_date: date
    funding: Decimal
    cost_ceiling: Optional[Decimal] = None
    fee_ceiling: Optional[Decimal] = None
    source_version_id: str = "BASE"

    def __post_init__(self):
        if self.funding < 0:
            raise ValueError("Funding cannot be negative")
        if self.cost_ceiling is not None and self.cost_ceiling < 0:
            raise ValueError("Cost ceiling cannot be negative")
        if self.fee_ceiling is not None and self.fee_ceiling < 0:
            raise ValueError("Fee ceiling cannot be negative")


@dataclass(frozen=True)
class Modification:
    modification_id: str
    effective_date: date
    resulting_funding: Optional[Decimal] = None
    resulting_cost_ceiling: Optional[Decimal] = None
    resulting_fee_ceiling: Optional[Decimal] = None
    evidence_supported: bool = False


def state_at(base: ContractEconomicState, modifications: Iterable[Modification], as_of: date) -> ContractEconomicState:
    state = base
    seen: set[str] = set()
    for mod in sorted(modifications, key=lambda item: (item.effective_date, item.modification_id)):
        if mod.modification_id in seen:
            raise ValueError(f"Duplicate modification id: {mod.modification_id}")
        seen.add(mod.modification_id)
        if mod.effective_date > as_of:
            continue
        if not mod.evidence_supported:
            raise ValueError(f"Modification {mod.modification_id} lacks supported evidence")
        funding = state.funding if mod.resulting_funding is None else mod.resulting_funding
        cost_ceiling = state.cost_ceiling if mod.resulting_cost_ceiling is None else mod.resulting_cost_ceiling
        fee_ceiling = state.fee_ceiling if mod.resulting_fee_ceiling is None else mod.resulting_fee_ceiling
        state = ContractEconomicState(
            effective_date=mod.effective_date,
            funding=money(funding),
            cost_ceiling=None if cost_ceiling is None else money(cost_ceiling),
            fee_ceiling=None if fee_ceiling is None else money(fee_ceiling),
            source_version_id=mod.modification_id,
        )
    return state


@dataclass(frozen=True)
class TaskOrder:
    order_id: str
    funding: Decimal
    cost_ceiling: Optional[Decimal]
    contract_terms_supported: bool
    evidence_ids: Tuple[str, ...]

    def __post_init__(self):
        if self.funding < 0:
            raise ValueError("Task-order funding cannot be negative")
        if self.cost_ceiling is not None and self.cost_ceiling < 0:
            raise ValueError("Task-order ceiling cannot be negative")
        if not self.evidence_ids:
            raise ValueError("Task order requires evidence lineage")


def constrain_order_candidate(order: TaskOrder, expected_increment: Decimal, already_billed: Decimal):
    if not order.contract_terms_supported:
        return {
            "order_id": order.order_id,
            "state": FindingState.UNKNOWN,
            "expected": None,
            "variance": None,
            "explanation": "Task-order terms are not supported.",
        }
    expected = money(expected_increment)
    if order.cost_ceiling is not None:
        expected = min(expected, money(order.cost_ceiling))
    billed = money(already_billed)
    variance = money(expected - billed)
    if variance > money(order.funding):
        return {
            "order_id": order.order_id,
            "state": FindingState.REQUIRES_REVIEW,
            "expected": expected,
            "variance": variance,
            "explanation": "Order-level candidate exceeds verified funding.",
        }
    if variance > 0:
        state = FindingState.RECOVERY_CANDIDATE
    elif variance < 0:
        state = FindingState.PAYABLE_CANDIDATE
    else:
        state = FindingState.NO_VARIANCE
    return {
        "order_id": order.order_id,
        "state": state,
        "expected": expected,
        "variance": variance,
        "explanation": "Order-level economics constrained by supported funding and ceiling.",
    }
