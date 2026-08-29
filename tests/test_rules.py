from datetime import date
import unittest

from govmargin.rules import (
    ContractContext,
    FAR_52_216_7_BILLING_RATE_ADJUSTMENT,
    FAR_52_216_7_COMPLETION_VOUCHER,
    RULES,
)


class RegulatoryRuleTests(unittest.TestCase):
    def test_clause_gates_applicability(self):
        context = ContractContext(frozenset({"52.216-7"}), date(2025, 1, 1))
        self.assertTrue(FAR_52_216_7_COMPLETION_VOUCHER.applies_to(context))

    def test_missing_clause_fails_closed(self):
        context = ContractContext(frozenset(), date(2025, 1, 1))
        self.assertFalse(FAR_52_216_7_BILLING_RATE_ADJUSTMENT.applies_to(context))

    def test_pre_version_contract_does_not_auto_apply_current_rule(self):
        context = ContractContext(frozenset({"52.216-7"}), date(2010, 1, 1))
        self.assertFalse(FAR_52_216_7_COMPLETION_VOUCHER.applies_to(context))

    def test_every_rule_has_evidence_requirements(self):
        for rule in RULES.values():
            self.assertTrue(rule.source.startswith("https://"))
            self.assertTrue(rule.section)
            self.assertTrue(rule.source_version)
            self.assertTrue(rule.required_evidence)
            self.assertTrue(rule.exclusions)


if __name__ == "__main__":
    unittest.main()
