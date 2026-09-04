from decimal import Decimal
import unittest

from govmargin.engine import (
    FindingState,
    IndirectTrueUpInput,
    RateState,
    SupportState,
    compute_indirect_true_up,
)


D = Decimal
SUPPORTED = SupportState.SUPPORTED


class IndirectTrueUpTests(unittest.TestCase):
    def base_case(self, **overrides):
        data = dict(
            contract_id="C-001",
            period="FY2025",
            allocation_base=D("1000000"),
            final_rate=D("0.25"),
            billed_indirect=D("200000"),
            rate_state=RateState.SETTLED_FINAL,
            contract_terms=SUPPORTED,
            base_allowability=SUPPORTED,
            base_allocability=SUPPORTED,
            indirect_ceiling_amount=None,
            remaining_funding=D("100000"),
        )
        data.update(overrides)
        return IndirectTrueUpInput(**data)

    def test_higher_final_rate_creates_candidate(self):
        result = compute_indirect_true_up(self.base_case())
        self.assertEqual(result.state, FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result.variance, D("50000.00"))

    def test_lower_final_economics_flags_payable(self):
        result = compute_indirect_true_up(self.base_case(billed_indirect=D("300000")))
        self.assertEqual(result.state, FindingState.PAYABLE_CANDIDATE)
        self.assertEqual(result.variance, D("-50000.00"))

    def test_already_billed_has_no_variance(self):
        result = compute_indirect_true_up(self.base_case(billed_indirect=D("250000")))
        self.assertEqual(result.state, FindingState.NO_VARIANCE)
        self.assertEqual(result.variance, D("0.00"))

    def test_unsettled_rate_requires_review(self):
        result = compute_indirect_true_up(self.base_case(rate_state=RateState.PROPOSED_FINAL))
        self.assertEqual(result.state, FindingState.REQUIRES_REVIEW)
        self.assertIsNone(result.variance)

    def test_unknown_contract_terms_fail_closed(self):
        result = compute_indirect_true_up(self.base_case(contract_terms=SupportState.UNKNOWN))
        self.assertEqual(result.state, FindingState.UNKNOWN)
        self.assertIsNone(result.expected_indirect)

    def test_funding_shortfall_requires_review(self):
        result = compute_indirect_true_up(self.base_case(remaining_funding=D("10000")))
        self.assertEqual(result.state, FindingState.REQUIRES_REVIEW)
        self.assertEqual(result.variance, D("50000.00"))

    def test_ceiling_caps_expected_economics(self):
        result = compute_indirect_true_up(self.base_case(indirect_ceiling_amount=D("220000")))
        self.assertEqual(result.state, FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result.variance, D("20000.00"))

    def test_ceiling_prevents_false_recovery(self):
        result = compute_indirect_true_up(
            self.base_case(
                indirect_ceiling_amount=D("200000"),
                billed_indirect=D("200000"),
            )
        )
        self.assertEqual(result.state, FindingState.NO_VARIANCE)
        self.assertEqual(result.variance, D("0.00"))

    def test_negative_numeric_input_never_creates_recovery(self):
        result = compute_indirect_true_up(self.base_case(allocation_base=D("-100")))
        self.assertEqual(result.state, FindingState.REQUIRES_REVIEW)
        self.assertIsNone(result.variance)

    def test_nonfinite_numeric_input_never_creates_recovery(self):
        result = compute_indirect_true_up(self.base_case(final_rate=D("NaN")))
        self.assertEqual(result.state, FindingState.REQUIRES_REVIEW)
        self.assertIsNone(result.billed_indirect)


if __name__ == "__main__":
    unittest.main()
