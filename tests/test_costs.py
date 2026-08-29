from decimal import Decimal
import unittest

from govmargin.costs import (
    AllowabilityState,
    ContractBillability,
    DirectCostInput,
    PaymentInput,
    compute_direct_cost_variance,
    compute_payment_shortfall,
)
from govmargin.engine import FindingState, SupportState

D = Decimal


class DirectCostTests(unittest.TestCase):
    def base_case(self, **overrides):
        data = dict(
            contract_id="C-ODC",
            transaction_id="T-1",
            amount=D("1000"),
            billed_amount=D("0"),
            allowability=AllowabilityState.SUPPORTED_ALLOWABLE,
            allocability=SupportState.SUPPORTED,
            contract_billability=ContractBillability.BILLABLE,
            duplicate=False,
            remaining_cost_ceiling=None,
            remaining_funding=D("5000"),
        )
        data.update(overrides)
        return DirectCostInput(**data)

    def test_supported_unbilled_odc_can_be_candidate(self):
        result = compute_direct_cost_variance(self.base_case())
        self.assertEqual(result.state, FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result.variance, D("1000.00"))

    def test_unallowable_cost_never_becomes_recovery(self):
        result = compute_direct_cost_variance(
            self.base_case(allowability=AllowabilityState.SUPPORTED_UNALLOWABLE)
        )
        self.assertNotEqual(result.state, FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result.expected_billable, D("0.00"))

    def test_contractually_nonbillable_odc_never_becomes_recovery(self):
        result = compute_direct_cost_variance(
            self.base_case(contract_billability=ContractBillability.NOT_BILLABLE)
        )
        self.assertEqual(result.state, FindingState.NO_VARIANCE)

    def test_unknown_allowability_fails_closed(self):
        result = compute_direct_cost_variance(
            self.base_case(allowability=AllowabilityState.UNKNOWN)
        )
        self.assertEqual(result.state, FindingState.UNKNOWN)

    def test_duplicate_is_excluded(self):
        result = compute_direct_cost_variance(self.base_case(duplicate=True))
        self.assertEqual(result.state, FindingState.NO_VARIANCE)
        self.assertIsNone(result.variance)

    def test_direct_cost_ceiling_caps_candidate(self):
        result = compute_direct_cost_variance(
            self.base_case(remaining_cost_ceiling=D("400"))
        )
        self.assertEqual(result.state, FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result.variance, D("400.00"))

    def test_funding_shortfall_requires_review(self):
        result = compute_direct_cost_variance(
            self.base_case(remaining_funding=D("50"))
        )
        self.assertEqual(result.state, FindingState.REQUIRES_REVIEW)

    def test_unallowable_amount_already_billed_flags_payable(self):
        result = compute_direct_cost_variance(
            self.base_case(
                billed_amount=D("500"),
                allowability=AllowabilityState.SUPPORTED_UNALLOWABLE,
            )
        )
        self.assertEqual(result.state, FindingState.PAYABLE_CANDIDATE)
        self.assertEqual(result.variance, D("-500.00"))


class PaymentTests(unittest.TestCase):
    def test_payment_shortfall(self):
        result = compute_payment_shortfall(
            PaymentInput("I-1", D("1000"), D("700"), True, True)
        )
        self.assertEqual(result["state"], FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result["variance"], D("300.00"))

    def test_disputed_shortfall_requires_review(self):
        result = compute_payment_shortfall(
            PaymentInput("I-1", D("1000"), D("700"), True, True, True)
        )
        self.assertEqual(result["state"], FindingState.REQUIRES_REVIEW)

    def test_payment_evidence_missing_fails_closed(self):
        result = compute_payment_shortfall(
            PaymentInput("I-1", D("1000"), D("700"), True, False)
        )
        self.assertEqual(result["state"], FindingState.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
