from decimal import Decimal

from govmargin.funding import (
    FundingClause,
    FundingSafeguardInput,
    FundingState,
    evaluate_funding_safeguard,
)


def test_limitation_of_cost_uses_estimated_cost_not_allotted_funds():
    result = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=FundingClause.LIMITATION_OF_COST,
            costs_incurred=Decimal("700"),
            expected_next_notice_window_costs=Decimal("60"),
            estimated_cost=Decimal("1000"),
            allotted_funds=Decimal("100"),
        )
    )
    assert result.verified_limit == Decimal("1000")
    assert result.threshold_amount == Decimal("750.00")
    assert result.state is FundingState.NOTICE_THRESHOLD_REACHED
    assert not result.automatic_recovery_allowed


def test_limitation_of_funds_uses_actual_allotment_and_fails_closed_above_it():
    result = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=FundingClause.LIMITATION_OF_FUNDS,
            costs_incurred=Decimal("805"),
            expected_next_notice_window_costs=Decimal("10"),
            estimated_cost=Decimal("2000"),
            allotted_funds=Decimal("800"),
        )
    )
    assert result.verified_limit == Decimal("800")
    assert result.state is FundingState.FUNDING_EXHAUSTED_REVIEW_REQUIRED
    assert not result.automatic_recovery_allowed


def test_projected_crossing_of_limit_is_notice_not_recovery():
    result = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=FundingClause.LIMITATION_OF_FUNDS,
            costs_incurred=Decimal("740"),
            expected_next_notice_window_costs=Decimal("100"),
            allotted_funds=Decimal("800"),
        )
    )
    assert result.state is FundingState.NOTICE_THRESHOLD_REACHED
    assert result.projected_cost_at_notice_window == Decimal("840")
    assert not result.automatic_recovery_allowed


def test_supported_clause_variations_are_explicit_and_bounded():
    supported = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=FundingClause.LIMITATION_OF_COST,
            costs_incurred=Decimal("700"),
            expected_next_notice_window_costs=Decimal("100"),
            estimated_cost=Decimal("1000"),
            notice_threshold_percent=Decimal("0.80"),
            notice_window_days=45,
        )
    )
    assert supported.threshold_amount == Decimal("800.00")
    assert supported.state is FundingState.NOTICE_THRESHOLD_REACHED

    bad_threshold = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=FundingClause.LIMITATION_OF_COST,
            costs_incurred=Decimal("1"),
            expected_next_notice_window_costs=Decimal("1"),
            estimated_cost=Decimal("100"),
            notice_threshold_percent=Decimal("0.90"),
        )
    )
    assert bad_threshold.state is FundingState.REQUIRES_REVIEW

    bad_window = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=FundingClause.LIMITATION_OF_COST,
            costs_incurred=Decimal("1"),
            expected_next_notice_window_costs=Decimal("1"),
            estimated_cost=Decimal("100"),
            notice_window_days=10,
        )
    )
    assert bad_window.state is FundingState.REQUIRES_REVIEW


def test_missing_clause_or_limit_never_creates_recovery():
    missing_clause = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=None,
            costs_incurred=Decimal("100"),
            expected_next_notice_window_costs=Decimal("100"),
        )
    )
    assert missing_clause.state is FundingState.UNKNOWN
    assert not missing_clause.automatic_recovery_allowed

    missing_limit = evaluate_funding_safeguard(
        FundingSafeguardInput(
            clause=FundingClause.LIMITATION_OF_FUNDS,
            costs_incurred=Decimal("100"),
            expected_next_notice_window_costs=Decimal("100"),
        )
    )
    assert missing_limit.state is FundingState.UNKNOWN
    assert not missing_limit.automatic_recovery_allowed
