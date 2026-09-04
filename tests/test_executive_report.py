import json
import unittest
from decimal import Decimal
from pathlib import Path

from aviation_io import evaluate_payload
from claim_workflow import ClaimLifecycle, ClaimRecord
from executive_report import render_executive_markdown


class ExecutiveReportTests(unittest.TestCase):
    def test_report_separates_settled_claim_ready_and_blocked_value(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        evaluated = evaluate_payload(payload)
        workflows = [
            ClaimRecord(
                claim_id="SYNTH-C-001",
                lifecycle=ClaimLifecycle.SETTLED,
                currency="USD",
                asserted_recovery_amount=Decimal("900000"),
                verified_settled_amount=Decimal("875000"),
            )
        ]

        report = render_executive_markdown(evaluated, workflows)
        self.assertIn("Verified settled recovery:** USD 875,000.00", report)
        self.assertIn("Claim-ready economic value:** USD 1,125,000.00", report)
        self.assertIn("Blocked potential:** USD 220,000.00", report)
        self.assertIn("missing_evidence:workscope", report)
        self.assertIn("SYNTH-C-001", report)

    def test_report_rejects_mixed_settlement_currency(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        evaluated = evaluate_payload(payload)
        workflows = [
            ClaimRecord(
                claim_id="SYNTH-C-001",
                lifecycle=ClaimLifecycle.SETTLED,
                currency="EUR",
                asserted_recovery_amount=Decimal("900000"),
                verified_settled_amount=Decimal("875000"),
            )
        ]
        with self.assertRaisesRegex(ValueError, "currency differs"):
            render_executive_markdown(evaluated, workflows)


if __name__ == "__main__":
    unittest.main()
