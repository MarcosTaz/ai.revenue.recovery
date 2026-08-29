from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

MONEY = Decimal("0.01")


def net_exposure(quantity: str, unit_cost: str, mitigation: str = "0", reimbursed: str = "0") -> str:
    gross = Decimal(quantity) * Decimal(unit_cost)
    result = gross - Decimal(mitigation) - Decimal(reimbursed)
    return str(result.quantize(MONEY, rounding=ROUND_HALF_UP))


def capped_claim(net: str, cap: str | None) -> str:
    value = Decimal(net)
    if cap is not None:
        value = min(value, Decimal(cap))
    return str(value.quantize(MONEY, rounding=ROUND_HALF_UP))
