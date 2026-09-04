import unittest
from decimal import Decimal

from govmargin.quick_closeout import (
    QuickCloseoutInput,
    QuickCloseoutState,
    assess_quick_closeout,
)


class QuickCloseoutTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            contract_id="C-1",
            physically_complete=True,
            total_contract_amount=Decimal("5000000"),
            unsettled_direct_and_indirect_costs=Decimal("400000"),
            risk_assessment_completed=True,
            risk_assessment_supports_use=True,
            reasonable_estimate_agreement_reachable=True,
            special_recovery_limitation_identified=False,
            evidence_complete=True,
        )
        data.update(overrides)
        return QuickCloseoutInput(**data)

    def test_eligible_case_reaches_human_review_only(self):
        result = assess_quick_closeout(self.base())
        self.assertEqual(result.state, QuickCloseoutState.ELIGIBLE_FOR_CO_REVIEW)
        self.assertEqual(result.threshold_amount, Decimal("500000.0"))

    def test_lesser_of_one_million_or_ten_percent_is_enforced(self):
        result = assess_quick_closeout(
            self.base(
                total_contract_amount=Decimal("20000000"),
                unsettled_direct_and_indirect_costs=Decimal("1000001"),
            )
        )
        self.assertEqual(result.threshold_amount, Decimal("1000000"))
        self.assertEqual(result.state, QuickCloseoutState.NOT_ELIGIBLE)

    def test_not_physically_complete_fails_closed(self):
        self.assertEqual(
            assess_quick_closeout(self.base(physically_complete=False)).state,
            QuickCloseoutState.NOT_ELIGIBLE,
        )

    def test_missing_risk_facts_are_unknown(self):
        self.assertEqual(
            assess_quick_closeout(self.base(risk_assessment_completed=None)).state,
            QuickCloseoutState.UNKNOWN,
        )

    def test_special_recovery_limitation_requires_review(self):
        self.assertEqual(
            assess_quick_closeout(self.base(special_recovery_limitation_identified=True)).state,
            QuickCloseoutState.REQUIRES_REVIEW,
        )

    def test_invalid_amounts_do_not_create_eligibility(self):
        self.assertEqual(
            assess_quick_closeout(self.base(total_contract_amount=Decimal("-1"))).state,
            QuickCloseoutState.REQUIRES_REVIEW,
        )


if __name__ == "__main__":
    unittest.main()
