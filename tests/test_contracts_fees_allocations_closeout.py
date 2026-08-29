from datetime import date
from decimal import Decimal
import unittest

from govmargin.allocations import IndirectLayer, compute_multi_pool
from govmargin.closeout import FinalVoucherInput, ReleaseState, reconcile_final_voucher
from govmargin.contracts import ContractEconomicState, Modification, TaskOrder, constrain_order_candidate, state_at
from govmargin.engine import FindingState, RateState
from govmargin.fees import FeeInput, FeeMethod, compute_fee_variance

D = Decimal


class ModificationTests(unittest.TestCase):
    def test_supported_modification_changes_funding_and_ceiling(self):
        base = ContractEconomicState(date(2025, 1, 1), D("1000"), D("800"), source_version_id="BASE")
        mod = Modification("M1", date(2025, 6, 1), D("1500"), D("1200"), evidence_supported=True)
        state = state_at(base, [mod], date(2025, 7, 1))
        self.assertEqual(state.funding, D("1500.00"))
        self.assertEqual(state.cost_ceiling, D("1200.00"))
        self.assertEqual(state.source_version_id, "M1")

    def test_unsupported_modification_is_rejected(self):
        base = ContractEconomicState(date(2025, 1, 1), D("1000"))
        mod = Modification("M1", date(2025, 6, 1), D("1500"), evidence_supported=False)
        with self.assertRaises(ValueError):
            state_at(base, [mod], date(2025, 7, 1))

    def test_future_modification_does_not_apply(self):
        base = ContractEconomicState(date(2025, 1, 1), D("1000"))
        mod = Modification("M1", date(2025, 6, 1), D("1500"), evidence_supported=True)
        state = state_at(base, [mod], date(2025, 5, 1))
        self.assertEqual(state.funding, D("1000"))

    def test_order_level_limit_prevents_cross_order_entitlement(self):
        order = TaskOrder("TO-1", D("100"), D("500"), True, ("e1",))
        result = constrain_order_candidate(order, D("500"), D("300"))
        self.assertEqual(result["state"], FindingState.REQUIRES_REVIEW)


class FeeTests(unittest.TestCase):
    def test_fixed_fee_balance(self):
        result = compute_fee_variance(FeeInput("C", FeeMethod.FIXED_AMOUNT, True, D("800"), fixed_fee_amount=D("1000")))
        self.assertEqual(result["state"], FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result["variance"], D("200.00"))

    def test_fee_ceiling_prevents_false_recovery(self):
        result = compute_fee_variance(FeeInput("C", FeeMethod.FIXED_AMOUNT, True, D("900"), fixed_fee_amount=D("1000"), fee_ceiling=D("900")))
        self.assertEqual(result["state"], FindingState.NO_VARIANCE)

    def test_unknown_fee_terms_fail_closed(self):
        result = compute_fee_variance(FeeInput("C", FeeMethod.UNKNOWN, False, D("0")))
        self.assertEqual(result["state"], FindingState.UNKNOWN)


class AllocationTests(unittest.TestCase):
    def test_multiple_supported_pools_are_reproducible(self):
        result = compute_multi_pool([
            IndirectLayer("fringe", D("1000"), D("0.2"), RateState.SETTLED_FINAL, True, True),
            IndirectLayer("overhead", D("1500"), D("0.3"), RateState.SETTLED_FINAL, True, True, ("fringe",)),
        ])
        self.assertEqual(result["total"], D("650.00"))

    def test_wrong_pool_support_requires_review(self):
        result = compute_multi_pool([
            IndirectLayer("g&a", D("1000"), D("0.1"), RateState.SETTLED_FINAL, False, True),
        ])
        self.assertEqual(result["state"], FindingState.REQUIRES_REVIEW)

    def test_cycle_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_multi_pool([
                IndirectLayer("a", D("1"), D("1"), RateState.SETTLED_FINAL, True, True, ("b",)),
                IndirectLayer("b", D("1"), D("1"), RateState.SETTLED_FINAL, True, True, ("a",)),
            ])


class CloseoutTests(unittest.TestCase):
    def test_missing_final_voucher_amount_can_be_candidate_before_release(self):
        result = reconcile_final_voucher(FinalVoucherInput("C", D("1000"), D("800"), True, True, ReleaseState.NOT_SIGNED, date(2026, 1, 1), True))
        self.assertEqual(result["state"], FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result["variance"], D("200.00"))

    def test_signed_release_requires_legal_review(self):
        result = reconcile_final_voucher(FinalVoucherInput("C", D("1000"), D("800"), True, True, ReleaseState.SIGNED_GENERAL, date(2026, 1, 1), True))
        self.assertEqual(result["state"], FindingState.REQUIRES_REVIEW)

    def test_incomplete_evidence_is_unknown(self):
        result = reconcile_final_voucher(FinalVoucherInput("C", D("1000"), D("800"), True, True, ReleaseState.NOT_SIGNED, None, False))
        self.assertEqual(result["state"], FindingState.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
