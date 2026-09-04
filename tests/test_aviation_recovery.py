import unittest
from datetime import date
from decimal import Decimal

from aviation_recovery import (
    ClaimInput,
    EntitlementRule,
    EntitlementType,
    EvidenceRef,
    Formula,
    Status,
    evaluate_claim,
    evaluate_portfolio,
    summarize_recovery,
)


INVOICE = EvidenceRef("E-INV-1", "invoice", "MRO invoice")
WORKSCOPE = EvidenceRef("E-WS-1", "workscope", "shop visit workscope")
PAYMENT = EvidenceRef("E-PAY-1", "payment_proof", "bank/payment ledger")


class AviationRecoveryEngineTests(unittest.TestCase):
    def test_maintenance_reserve_lower_of_cost_and_fund(self):
        rule = EntitlementRule(
            rule_id="LEASE-A-MR-ENGINE-2026",
            entitlement_type=EntitlementType.MAINTENANCE_RESERVE,
            formula=Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND,
            currency="USD",
            effective_from=date(2026, 1, 1),
            required_evidence_types=("invoice", "workscope", "payment_proof"),
            deadline_days_after_event=120,
        )
        claim = ClaimInput(
            claim_id="C-001",
            rule_id=rule.rule_id,
            event_date=date(2026, 6, 1),
            evaluation_date=date(2026, 7, 1),
            eligible_cost=Decimal("1250000"),
            available_fund=Decimal("900000"),
            evidence=(INVOICE, WORKSCOPE, PAYMENT),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.CLAIM_READY)
        self.assertEqual(result.gross_entitlement, Decimal("900000.00"))
        self.assertEqual(result.net_recoverable, Decimal("900000.00"))

    def test_prior_reimbursement_is_not_double_recovered(self):
        rule = EntitlementRule(
            rule_id="LEASE-B-LC-2026",
            entitlement_type=EntitlementType.LESSOR_CONTRIBUTION,
            formula=Formula.PERCENT_OF_ELIGIBLE_COST,
            currency="USD",
            effective_from=date(2026, 1, 1),
            contribution_rate=Decimal("0.50"),
            cap=Decimal("400000"),
            required_evidence_types=("invoice",),
        )
        claim = ClaimInput(
            claim_id="C-002",
            rule_id=rule.rule_id,
            event_date=date(2026, 3, 1),
            evaluation_date=date(2026, 3, 15),
            eligible_cost=Decimal("1000000"),
            prior_paid_or_reimbursed=Decimal("125000"),
            claimed_to_date=Decimal("50000"),
            evidence=(INVOICE,),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.gross_entitlement, Decimal("400000.00"))
        self.assertEqual(result.net_recoverable, Decimal("225000.00"))
        self.assertEqual(result.status, Status.CLAIM_READY)

    def test_missing_evidence_blocks_claim(self):
        rule = EntitlementRule(
            rule_id="LEASE-C-MR-2026",
            entitlement_type=EntitlementType.MAINTENANCE_RESERVE,
            formula=Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND,
            currency="USD",
            effective_from=date(2026, 1, 1),
            required_evidence_types=("invoice", "workscope"),
        )
        claim = ClaimInput(
            claim_id="C-003",
            rule_id=rule.rule_id,
            event_date=date(2026, 2, 1),
            evaluation_date=date(2026, 2, 10),
            eligible_cost=Decimal("250000"),
            available_fund=Decimal("250000"),
            evidence=(INVOICE,),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.BLOCKED)
        self.assertIn("missing_evidence:workscope", result.blocking_issues)

    def test_deadline_expiry_blocks_claim(self):
        rule = EntitlementRule(
            rule_id="LEASE-D-LC-2026",
            entitlement_type=EntitlementType.LESSOR_CONTRIBUTION,
            formula=Formula.PERCENT_OF_ELIGIBLE_COST,
            currency="USD",
            effective_from=date(2026, 1, 1),
            contribution_rate=Decimal("1"),
            deadline_days_after_event=30,
        )
        claim = ClaimInput(
            claim_id="C-004",
            rule_id=rule.rule_id,
            event_date=date(2026, 1, 1),
            evaluation_date=date(2026, 2, 15),
            eligible_cost=Decimal("100000"),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.BLOCKED)
        self.assertIn("contractual_deadline_expired", result.blocking_issues)

    def test_approaching_deadline_requires_review(self):
        rule = EntitlementRule(
            rule_id="LEASE-E-LC-2026",
            entitlement_type=EntitlementType.LESSOR_CONTRIBUTION,
            formula=Formula.FIXED_AMOUNT,
            currency="USD",
            effective_from=date(2026, 1, 1),
            fixed_amount=Decimal("75000"),
            deadline_days_after_event=90,
        )
        claim = ClaimInput(
            claim_id="C-005",
            rule_id=rule.rule_id,
            event_date=date(2026, 1, 1),
            evaluation_date=date(2026, 3, 15),
            eligible_cost=Decimal("80000"),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.REVIEW_REQUIRED)
        self.assertTrue(any(item.startswith("deadline_approaching:") for item in result.warnings))

    def test_excluded_cost_category_blocks_claim(self):
        rule = EntitlementRule(
            rule_id="LEASE-F-COSTSHARE-2026",
            entitlement_type=EntitlementType.COST_SHARING,
            formula=Formula.PERCENT_OF_ELIGIBLE_COST,
            currency="USD",
            effective_from=date(2026, 1, 1),
            contribution_rate=Decimal("0.25"),
            excluded_cost_categories=("betterment", "late_fee"),
        )
        claim = ClaimInput(
            claim_id="C-006",
            rule_id=rule.rule_id,
            event_date=date(2026, 4, 1),
            evaluation_date=date(2026, 4, 2),
            eligible_cost=Decimal("200000"),
            cost_categories=("labor", "betterment"),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.BLOCKED)
        self.assertIn("excluded_cost_category_present:betterment", result.blocking_issues)

    def test_evaluation_date_before_event_blocks_candidate(self):
        rule = EntitlementRule(
            rule_id="LEASE-CHRONOLOGY-2026",
            entitlement_type=EntitlementType.LESSOR_CONTRIBUTION,
            formula=Formula.PERCENT_OF_ELIGIBLE_COST,
            currency="USD",
            effective_from=date(2026, 1, 1),
            contribution_rate=Decimal("0.50"),
            required_evidence_types=("invoice",),
        )
        claim = ClaimInput(
            claim_id="C-CHRONOLOGY",
            rule_id=rule.rule_id,
            event_date=date(2026, 6, 15),
            evaluation_date=date(2026, 6, 1),
            eligible_cost=Decimal("100000"),
            evidence=(INVOICE,),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.BLOCKED)
        self.assertIn("evaluation_date_precedes_event_date", result.blocking_issues)

    def test_malformed_required_evidence_reference_blocks_candidate(self):
        rule = EntitlementRule(
            rule_id="LEASE-EVIDENCE-2026",
            entitlement_type=EntitlementType.MAINTENANCE_RESERVE,
            formula=Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND,
            currency="USD",
            effective_from=date(2026, 1, 1),
            required_evidence_types=("invoice",),
        )
        malformed_invoice = EvidenceRef("E-BAD", "invoice", "   ")
        claim = ClaimInput(
            claim_id="C-EVIDENCE",
            rule_id=rule.rule_id,
            event_date=date(2026, 5, 1),
            evaluation_date=date(2026, 5, 2),
            eligible_cost=Decimal("100000"),
            available_fund=Decimal("100000"),
            evidence=(malformed_invoice,),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.BLOCKED)
        self.assertIn("evidence_ref_1_missing_source_name", result.blocking_issues)
        self.assertIn("missing_evidence:invoice", result.blocking_issues)

    def test_unknown_rule_is_blocked_in_portfolio(self):
        claim = ClaimInput(
            claim_id="C-007",
            rule_id="MISSING",
            event_date=date(2026, 1, 1),
            evaluation_date=date(2026, 1, 2),
            eligible_cost=Decimal("100"),
        )
        result = evaluate_portfolio({}, [claim])[0]
        self.assertEqual(result.status, Status.BLOCKED)
        self.assertEqual(result.blocking_issues, ("unknown_rule_id",))

    def test_single_currency_portfolio_summary(self):
        rule = EntitlementRule(
            rule_id="LEASE-G-2026",
            entitlement_type=EntitlementType.SECURITY_DEPOSIT_RELEASE,
            formula=Formula.FIXED_AMOUNT,
            currency="USD",
            effective_from=date(2026, 1, 1),
            fixed_amount=Decimal("300000"),
        )
        claim = ClaimInput(
            claim_id="C-008",
            rule_id=rule.rule_id,
            event_date=date(2026, 8, 1),
            evaluation_date=date(2026, 8, 2),
            eligible_cost=Decimal("0"),
        )
        summary = summarize_recovery(evaluate_portfolio({rule.rule_id: rule}, [claim]))
        self.assertEqual(summary["claim_ready_count"], 1)
        self.assertEqual(summary["net_recoverable"], Decimal("300000.00"))


if __name__ == "__main__":
    unittest.main()
