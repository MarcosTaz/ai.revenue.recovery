from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MONEY = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("non-finite economic input")
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PilotEconomicsInput:
    fixed_fee: Decimal
    delivery_hours: Decimal
    loaded_hourly_cost: Decimal
    software_variable_cost: Decimal = Decimal("0")
    partner_share: Decimal = Decimal("0")
    other_direct_cost: Decimal = Decimal("0")


@dataclass(frozen=True)
class PilotEconomicsResult:
    revenue: Decimal
    labor_cost: Decimal
    partner_cost: Decimal
    direct_cost: Decimal
    gross_profit: Decimal
    gross_margin: Decimal
    effective_revenue_per_delivery_hour: Decimal | None


def calculate_pilot_economics(case: PilotEconomicsInput) -> PilotEconomicsResult:
    values = (
        case.fixed_fee,
        case.delivery_hours,
        case.loaded_hourly_cost,
        case.software_variable_cost,
        case.partner_share,
        case.other_direct_cost,
    )
    if any((not value.is_finite()) or value < 0 for value in values):
        raise ValueError("pilot economic inputs must be finite and nonnegative")
    if case.partner_share > 1:
        raise ValueError("partner_share must be between 0 and 1")

    revenue = money(case.fixed_fee)
    labor_cost = money(case.delivery_hours * case.loaded_hourly_cost)
    partner_cost = money(revenue * case.partner_share)
    direct_cost = money(labor_cost + case.software_variable_cost + partner_cost + case.other_direct_cost)
    gross_profit = money(revenue - direct_cost)
    gross_margin = Decimal("0") if revenue == 0 else (gross_profit / revenue).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    per_hour = None if case.delivery_hours == 0 else money(revenue / case.delivery_hours)
    return PilotEconomicsResult(
        revenue=revenue,
        labor_cost=labor_cost,
        partner_cost=partner_cost,
        direct_cost=direct_cost,
        gross_profit=gross_profit,
        gross_margin=gross_margin,
        effective_revenue_per_delivery_hour=per_hour,
    )


def maximum_delivery_hours_for_margin(
    fixed_fee: Decimal,
    loaded_hourly_cost: Decimal,
    target_gross_margin: Decimal,
    nonlabor_direct_cost: Decimal = Decimal("0"),
) -> Decimal:
    values = (fixed_fee, loaded_hourly_cost, target_gross_margin, nonlabor_direct_cost)
    if any(not value.is_finite() for value in values):
        raise ValueError("inputs must be finite")
    if fixed_fee < 0 or loaded_hourly_cost <= 0 or nonlabor_direct_cost < 0:
        raise ValueError("invalid economic inputs")
    if target_gross_margin < 0 or target_gross_margin >= 1:
        raise ValueError("target_gross_margin must be >= 0 and < 1")

    allowed_direct_cost = fixed_fee * (Decimal("1") - target_gross_margin)
    labor_budget = allowed_direct_cost - nonlabor_direct_cost
    if labor_budget <= 0:
        return Decimal("0")
    return (labor_budget / loaded_hourly_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
