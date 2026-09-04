from datetime import date
import unittest

from govmargin.rules import (
    ContractContext,
    FAR_52_216_7_BILLING_RATE_ADJUSTMENT,
    FAR_52_216_7_COMPLETION_VOUCHER,
    FAR_52_216_7_FINAL_PAYMENT,
    FAR_52_232_20_EXCESS_LIMIT,
    FAR_52_232_20_NOTICE,
    FAR_52_232_22_EXCESS_LIMIT,
    FAR_52_232_22_NOTICE,
    RULES,
)


class RegulatoryRuleTests(unittest.TestCase):
    def test_clause_gates_applicability(self):
        context = ContractContext(frozenset({"52.216-7"}), date(2025, 1, 1))
        self.assertTrue(FAR_52_216_7_COMPLETION_VOUCHER.applies_to(context))
        self.assertTrue(FAR_52_216_7_FINAL_PAYMENT.applies_to(context))

    def test_missing_clause_fails_closed(self):
        context = ContractContext(frozenset(), date(2025, 1, 1))
        self.assertFalse(FAR_52_216_7_BILLING_RATE_ADJUSTMENT.applies_to(context))
        self.assertFalse(FAR_52_216_7_FINAL_PAYMENT.applies_to(context))
        self.assertFalse(FAR_52_232_20_NOTICE.applies_to(context))
        self.assertFalse(FAR_52_232_22_NOTICE.applies_to(context))

    def test_pre_version_contract_does_not_auto_apply_current_rule(self):
        context = ContractContext(frozenset({"52.216-7"}), date(2010, 1, 1))
        self.assertFalse(FAR_52_216_7_COMPLETION_VOUCHER.applies_to(context))
        self.assertFalse(FAR_52_216_7_FINAL_PAYMENT.applies_to(context))

    def test_final_payment_rule_requires_approval_and_compliance_evidence(self):
        required = FAR_52_216_7_FINAL_PAYMENT.required_evidence
        self.assertIn("approved_completion_voucher", required)
        self.assertIn("allowable_cost_support", required)
        self.assertIn("cumulative_payments", required)
        self.assertIn("contract_compliance_state", required)
        text = f"{FAR_52_216_7_FINAL_PAYMENT.test} {FAR_52_216_7_FINAL_PAYMENT.exclusions}".lower()
        self.assertIn("not", text)
        self.assertIn("automatic", text)

    def test_limitation_of_cost_rules_require_exact_clause(self):
        supported = ContractContext(frozenset({"52.232-20"}), date(2025, 1, 1))
        wrong_clause = ContractContext(frozenset({"52.232-22"}), date(2025, 1, 1))
        self.assertTrue(FAR_52_232_20_NOTICE.applies_to(supported))
        self.assertTrue(FAR_52_232_20_EXCESS_LIMIT.applies_to(supported))
        self.assertFalse(FAR_52_232_20_NOTICE.applies_to(wrong_clause))
        self.assertFalse(FAR_52_232_20_EXCESS_LIMIT.applies_to(wrong_clause))

    def test_limitation_of_funds_rules_require_exact_clause(self):
        supported = ContractContext(frozenset({"52.232-22"}), date(2025, 1, 1))
        wrong_clause = ContractContext(frozenset({"52.232-20"}), date(2025, 1, 1))
        self.assertTrue(FAR_52_232_22_NOTICE.applies_to(supported))
        self.assertTrue(FAR_52_232_22_EXCESS_LIMIT.applies_to(supported))
        self.assertFalse(FAR_52_232_22_NOTICE.applies_to(wrong_clause))
        self.assertFalse(FAR_52_232_22_EXCESS_LIMIT.applies_to(wrong_clause))

    def test_every_rule_has_evidence_requirements(self):
        for rule in RULES.values():
            self.assertTrue(rule.source.startswith("https://"))
            self.assertTrue(rule.section)
            self.assertTrue(rule.source_version)
            self.assertTrue(rule.required_evidence)
            self.assertTrue(rule.exclusions)

    def test_funding_rules_never_describe_notice_as_entitlement(self):
        for rule in (
            FAR_52_232_20_NOTICE,
            FAR_52_232_20_EXCESS_LIMIT,
            FAR_52_232_22_NOTICE,
            FAR_52_232_22_EXCESS_LIMIT,
        ):
            text = f"{rule.test} {rule.exclusions}".lower()
            self.assertTrue("not" in text or "do not" in text)
            self.assertTrue("receivable" in text or "entitlement" in text or "reimburs" in text)


if __name__ == "__main__":
    unittest.main()
