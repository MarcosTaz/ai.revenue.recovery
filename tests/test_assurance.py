from decimal import Decimal

from govmargin.assurance import AssuranceState, ContractAssuranceInput, compute_contract_assurance

D = Decimal


def _case(**overrides):
    data = dict(
        contract_id="C1",
        supported_expected_billing=D("1000"),
        cumulative_billed=D("1000"),
        cumulative_paid=D("1000"),
        evidence_complete=True,
        contract_terms_supported=True,
        allowability_supported=True,
        allocability_supported=True,
        funding_supported=True,
        ceiling_supported=True,
        final_rate_settled_when_required=True,
    )
    data.update(overrides)
    return ContractAssuranceInput(**data)


def test_current_supported_economics_are_current():
    result = compute_contract_assurance(_case())
    assert result.state is AssuranceState.CURRENT
    assert result.supported_unbilled == D("0.00")


def test_supported_unbilled_requires_all_economic_gates():
    result = compute_contract_assurance(_case(cumulative_billed=D("800"), cumulative_paid=D("800")))
    assert result.state is AssuranceState.SUPPORTED_UNBILLED
    assert result.supported_unbilled == D("200.00")

    funding_risk = compute_contract_assurance(_case(
        cumulative_billed=D("800"),
        cumulative_paid=D("800"),
        funding_supported=False,
    ))
    assert funding_risk.state is AssuranceState.AT_RISK
    assert funding_risk.supported_unbilled is None


def test_overbilling_is_payable_not_hidden():
    result = compute_contract_assurance(_case(cumulative_billed=D("1100"), cumulative_paid=D("1100")))
    assert result.state is AssuranceState.PAYABLE_EXPOSURE
    assert result.payable_exposure == D("100.00")


def test_payment_shortfall_is_separate_from_unbilled_revenue():
    result = compute_contract_assurance(_case(cumulative_paid=D("900")))
    assert result.state is AssuranceState.PAYMENT_SHORTFALL
    assert result.payment_shortfall == D("100.00")
    assert result.supported_unbilled == D("0.00")


def test_missing_evidence_or_rate_truth_fails_closed():
    missing = compute_contract_assurance(_case(evidence_complete=False))
    assert missing.state is AssuranceState.UNKNOWN

    unsettled = compute_contract_assurance(_case(final_rate_settled_when_required=False))
    assert unsettled.state is AssuranceState.REQUIRES_REVIEW


def test_expressly_unallowable_never_becomes_earned_revenue():
    result = compute_contract_assurance(_case(expressly_unallowable=True, cumulative_billed=D("500")))
    assert result.state is AssuranceState.NOT_ALLOWABLE
    assert result.earned_supported is None
    assert result.supported_unbilled is None


def test_procedural_risk_prevents_supported_unbilled_promotion():
    result = compute_contract_assurance(_case(
        cumulative_billed=D("800"),
        cumulative_paid=D("800"),
        procedural_risk=True,
    ))
    assert result.state is AssuranceState.AT_RISK
    assert result.supported_unbilled is None
