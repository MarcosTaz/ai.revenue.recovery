from govmargin.contract_type import Applicability, classify_contract_type


def test_cpff_requires_clause_and_settled_rate_evidence():
    missing_clause = classify_contract_type("CPFF", settled_final_rates_evidenced=True)
    assert missing_clause.applicability is Applicability.REVIEW_REQUIRED
    assert not missing_clause.enabled_for_recovery_engine

    missing_rates = classify_contract_type("cost plus fixed fee", clause_ids=["52.216-7"])
    assert missing_rates.applicability is Applicability.REVIEW_REQUIRED
    assert not missing_rates.enabled_for_recovery_engine

    supported = classify_contract_type(
        "Cost-Plus-Fixed-Fee",
        clause_ids=["FAR 52.232-20", "52.216-7"],
        settled_final_rates_evidenced=True,
    )
    assert supported.normalized_type == "CPFF"
    assert supported.applicability is Applicability.SUPPORTED_WEDGE
    assert supported.enabled_for_recovery_engine


def test_tm_and_labor_hour_are_explicitly_disabled_not_misclassified():
    for value in ("T&M", "time and materials", "labor hour", "LH"):
        decision = classify_contract_type(
            value,
            clause_ids=["52.216-7"],
            settled_final_rates_evidenced=True,
        )
        assert decision.applicability is Applicability.UNSUPPORTED
        assert not decision.enabled_for_recovery_engine


def test_fixed_price_unknown_and_missing_fail_closed():
    ffp = classify_contract_type("firm fixed price")
    assert ffp.normalized_type == "FFP"
    assert ffp.applicability is Applicability.UNSUPPORTED
    assert not ffp.enabled_for_recovery_engine

    unknown = classify_contract_type("hybrid bespoke")
    assert unknown.applicability is Applicability.UNKNOWN
    assert not unknown.enabled_for_recovery_engine

    missing = classify_contract_type(None)
    assert missing.normalized_type == "UNKNOWN"
    assert missing.applicability is Applicability.UNKNOWN
    assert not missing.enabled_for_recovery_engine
