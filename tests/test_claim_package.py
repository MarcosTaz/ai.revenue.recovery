import unittest
from datetime import date
from decimal import Decimal

from aviation_dossier import build_external_claim_dossier, build_internal_review_dossier
from aviation_recovery import (
    ClaimInput,
    EntitlementRule,
    EntitlementType,
    EvidenceRef,
    Formula,
    evaluate_claim,
)
from claim_package import render_external_claim_markdown


class ClaimPackageTests(unittest.TestCase):
    def _rule(self):
        return EntitlementRule(
            rule_id="SYNTH-MR-1",
            entitlement_type=EntitlementType.MAINTENANCE_RESERVE,
            formula=Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND,
            currency="USD",
            effective_from=date(2026, 1, 1),
            required_evidence_types=("invoice", "workscope", "payment_proof"),
        )

    def _claim(self, complete_lineage=True):
        refs = {
            "rule_source": "Lease.pdf#MR",
            "event_date": "Completion.pdf#p1",
            "eligible_cost": "Recon.xlsx#Eligible",
            "available_fund": "Reserve.pdf#Fund",
        }
        if not complete_lineage:
            refs.pop("available_fund")
        return ClaimInput(
            claim_id="C-1",
            rule_id="SYNTH-MR-1",
            event_date=date(2026, 6, 1),
            evaluation_date=date(2026, 6, 15),
            eligible_cost=Decimal("1000000"),
            available_fund=Decimal("800000"),
            evidence=(
                EvidenceRef("E1", "invoice", "MRO invoice"),
                EvidenceRef("E2", "workscope", "MRO workscope"),
                EvidenceRef("E3", "payment_proof", "payment ledger"),
            ),
            source_refs=refs,
        )

    def test_passed_dossier_renders_external_package(self):
        rule = self._rule()
        claim = self._claim()
        result = evaluate_claim(rule, claim)
        dossier = build_external_claim_dossier(rule, claim, result)
        package = render_external_claim_markdown(dossier)
        self.assertIn("Aviation Lease Entitlement Claim Package", package)
        self.assertIn("Net amount requested:** 800000.00", package)
        self.assertIn("Lease.pdf#MR", package)
        self.assertIn("E1", package)

    def test_internal_dossier_cannot_be_externalized(self):
        rule = self._rule()
        claim = self._claim(complete_lineage=False)
        result = evaluate_claim(rule, claim)
        dossier = build_internal_review_dossier(rule, claim, result)
        with self.assertRaisesRegex(ValueError, "externalization gate"):
            render_external_claim_markdown(dossier)


if __name__ == "__main__":
    unittest.main()
