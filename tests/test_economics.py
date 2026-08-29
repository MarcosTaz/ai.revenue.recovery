from decimal import Decimal

from govmargin.economics import (
    PilotEconomicsInput,
    calculate_pilot_economics,
    maximum_delivery_hours_for_margin,
)

D = Decimal


def test_design_partner_fixed_fee_margin_is_reproducible():
    result = calculate_pilot_economics(PilotEconomicsInput(
        fixed_fee=D("7500"),
        delivery_hours=D("40"),
        loaded_hourly_cost=D("75"),
        software_variable_cost=D("250"),
        other_direct_cost=D("250"),
    ))
    assert result.revenue == D("7500.00")
    assert result.labor_cost == D("3000.00")
    assert result.direct_cost == D("3500.00")
    assert result.gross_profit == D("4000.00")
    assert result.gross_margin == D("0.5333")
    assert result.effective_revenue_per_delivery_hour == D("187.50")


def test_partner_share_is_explicit_direct_cost():
    result = calculate_pilot_economics(PilotEconomicsInput(
        fixed_fee=D("10000"),
        delivery_hours=D("20"),
        loaded_hourly_cost=D("100"),
        partner_share=D("0.20"),
    ))
    assert result.partner_cost == D("2000.00")
    assert result.direct_cost == D("4000.00")
    assert result.gross_margin == D("0.6000")


def test_maximum_hours_for_target_margin_sets_delivery_guardrail():
    hours = maximum_delivery_hours_for_margin(
        fixed_fee=D("7500"),
        loaded_hourly_cost=D("75"),
        target_gross_margin=D("0.50"),
        nonlabor_direct_cost=D("500"),
    )
    assert hours == D("43.33")


def test_invalid_inputs_fail_closed():
    try:
        calculate_pilot_economics(PilotEconomicsInput(
            fixed_fee=D("7500"),
            delivery_hours=D("-1"),
            loaded_hourly_cost=D("75"),
        ))
    except ValueError:
        pass
    else:
        raise AssertionError("negative delivery hours must be rejected")

    try:
        maximum_delivery_hours_for_margin(D("7500"), D("75"), D("1.0"))
    except ValueError:
        pass
    else:
        raise AssertionError("100% target margin must be rejected")
