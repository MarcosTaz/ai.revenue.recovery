import json
import unittest
from decimal import Decimal
from pathlib import Path

from aviation_io import evaluate_payload
from claim_workflow import ClaimLifecycle, ClaimRecord
from executive_report import render_executive_markdown


class ExecutiveReportTests(unittest.TestCase):
    def setUp(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        self.evaluated = evaluate_payload(payload)

    def record(
        self,
        lifecycle: ClaimLifecycle,
        *,
        claim_id: str = "SYNTH-C-001",
        asserted: str = "900000",
        settled: str = "0",
        currency: str = "USD",
    ) -> ClaimRecord:
        return ClaimRecord(
            claim_id=claim_id,
            lifecycle=lifecycle,
            currency=currency,
            asserted_recovery_amount=Decimal(asserted),
            verified_settled_amount=Decimal(settled),
        )

    def test_settled_value_is_removed_from_claim_ready_bucket(self):
        report = render_executive_markdown(
            self.evaluated,
            [self.record(ClaimLifecycle.SETTLED, settled="875000")],
        )

        self.assertIn("Verified settled recovery:** USD 875,000.00", report)
        self.assertIn("Claim-ready, not yet submitted:** USD 225,000.00", report)
        self.assertIn("Submitted / in counterparty process, unsettled:** USD 0.00", report)
        self.assertIn("Blocked potential:** USD 220,000.00", report)
        self.assertNotIn("Claim-ready, not yet submitted:** USD 1,125,000.00", report)
        self.assertIn("| SYNTH-C-001 | claim_ready | settled |", report)

    def test_submitted_value_is_separate_from_claim_ready_and_recovery(self):
        report = render_executive_markdown(
            self.evaluated,
            [self.record(ClaimLifecycle.SUBMITTED)],
        )

        self.assertIn("Verified settled recovery:** USD 0.00", report)
        self.assertIn("Claim-ready, not yet submitted:** USD 225,000.00", report)
        self.assertIn(
            "Submitted / in counterparty process, unsettled:** USD 900,000.00",
            report,
        )
        self.assertIn("| SYNTH-C-001 | claim_ready | submitted |", report)

    def test_rejected_value_moves_to_workflow_review_bucket(self):
        report = render_executive_markdown(
            self.evaluated,
            [self.record(ClaimLifecycle.REJECTED)],
        )

        self.assertIn("Claim-ready, not yet submitted:** USD 225,000.00", report)
        self.assertIn("Workflow review / rejected:** USD 900,000.00", report)
        self.assertIn("Verified settled recovery:** USD 0.00", report)

    def test_no_workflow_preserves_current_claim_ready_summary(self):
        report = render_executive_markdown(self.evaluated)
        self.assertIn("Claim-ready, not yet submitted:** USD 1,125,000.00", report)
        self.assertIn("Verified settled recovery:** USD 0.00", report)

    def test_report_rejects_mixed_workflow_currency(self):
        with self.assertRaisesRegex(ValueError, "currency differs"):
            render_executive_markdown(
                self.evaluated,
                [self.record(ClaimLifecycle.SETTLED, settled="875000", currency="EUR")],
            )

    def test_report_rejects_stale_asserted_amount(self):
        with self.assertRaisesRegex(ValueError, "asserted amount differs"):
            render_executive_markdown(
                self.evaluated,
                [self.record(ClaimLifecycle.SUBMITTED, asserted="899999")],
            )

    def test_report_rejects_unknown_workflow_claim(self):
        with self.assertRaisesRegex(ValueError, "unknown claim"):
            render_executive_markdown(
                self.evaluated,
                [
                    self.record(
                        ClaimLifecycle.SUBMITTED,
                        claim_id="NOT-IN-COHORT",
                        asserted="1",
                    )
                ],
            )

    def test_report_rejects_duplicate_workflow_records(self):
        record = self.record(ClaimLifecycle.SUBMITTED)
        with self.assertRaisesRegex(ValueError, "duplicate workflow record"):
            render_executive_markdown(self.evaluated, [record, record])


if __name__ == "__main__":
    unittest.main()
