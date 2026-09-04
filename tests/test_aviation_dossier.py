import unittest
from datetime import date
from decimal import Decimal

from aviation_dossier import (
    DossierIntegrityError,
    build_external_claim_dossier,
    build_internal_review_dossier,
)
from aviation_recovery import (
    ClaimInput,
    EntitlementRule,
    EntitlementType,
    EvidenceRef,
    Formula,
    Status,
    evaluate_claim,
)


class AviationDossierTests(unittest.TestCase):
    def _rule(self):
        return EntitlementRule(
            rule_id="LEASE-A-MR-ENGINE-2026",
            entitlement_type=EntitlementType.MAINTENANCE_RESERVE,
            formula=Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND,
            currency="USD",
            effective_from=date(2026, 1, 1),
            required_evidence_types=("invoice", "workscope", "payment_proof"),
            deadline_days_after_event=120,
        )

    def _claim(self, source_refs=None, evidence=None):
        return ClaimInput(
            claim_id="C-001",
            rule_id="LEASE-A-MR-ENGINE-2026",
            event_date=date(2026, 6, 1),
            evaluation_date=date(2026, 7, 1),
            eligible_cost=Decimal("1250000"),
            available_fund=Decimal("900000"),
            evidence=evidence
            or (
                EvidenceRef("E-INV", "invoice", "MRO invoice"),
                EvidenceRef("E-WS", "workscope", "engine workscope"),
                EvidenceRef("E-PAY", "payment_proof", "finance ledger"),
            ),
            source_refs=source_refs or {},
        )

    def test_external_dossier_rejects_missing_lineage(self):
        rule = self._rule()
        claim = self._claim()
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.CLAIM_READY)
        with self.assertRaises(DossierIntegrityError):
            build_external_claim_dossier(rule, claim, result)

    def test_internal_dossier_exposes_lineage_gaps(self):
        rule = self._rule()
        claim = self._claim(source_refs={"rule_source": "Lease.pdf#Schedule-6"})
        result = evaluate_claim(rule, claim)
        dossier = build_internal_review_dossier(rule, claim, result)
        self.assertIn("missing_source_ref:event_date", dossier["lineage_gaps"])
        self.assertIn("missing_source_ref:eligible_cost", dossier["lineage_gaps"])
        self.assertIn("missing_source_ref:available_fund", dossier["lineage_gaps"])

    def test_external_dossier_passes_with_complete_lineage(self):
        rule = self._rule()
        claim = self._claim(
            source_refs={
                "rule_source": "Lease.pdf#Schedule-6",
                "event_date": "CompletionCertificate.pdf#p1",
                "eligible_cost": "EligibleCostReconciliation.xlsx#Summary",
                "available_fund": "ReserveStatement-2026-06.pdf#EngineFund",
            }
        )
        result = evaluate_claim(rule, claim)
        dossier = build_external_claim_dossier(rule, claim, result)
        self.assertEqual(dossier["externalization_gate"], "passed")
        self.assertEqual(dossier["lineage_gaps"], [])
        self.assertEqual(dossier["claim"]["net_recoverable"], "900000.00")

    def test_external_dossier_rejects_blocked_claim(self):
        rule = self._rule()
        claim = self._claim(
            source_refs={
                "rule_source": "Lease.pdf#Schedule-6",
                "event_date": "CompletionCertificate.pdf#p1",
                "eligible_cost": "EligibleCostReconciliation.xlsx#Summary",
                "available_fund": "ReserveStatement-2026-06.pdf#EngineFund",
            },
            evidence=(EvidenceRef("E-INV", "invoice", "MRO invoice"),),
        )
        result = evaluate_claim(rule, claim)
        self.assertEqual(result.status, Status.BLOCKED)
        with self.assertRaises(DossierIntegrityError):
            build_external_claim_dossier(rule, claim, result)


if __name__ == "__main__":
    unittest.main()
