import json
import unittest
from pathlib import Path

from aviation_io import evaluate_payload


class TAPSyntheticDemoTests(unittest.TestCase):
    def test_demo_separates_ready_review_and_blocked_value(self):
        payload = json.loads(Path("examples/tap_synthetic_demo.json").read_text(encoding="utf-8"))
        evaluated = evaluate_payload(payload)
        summary = evaluated["summary"]

        self.assertEqual(summary["currency"], "EUR")
        self.assertEqual(summary["candidate_count"], 4)
        self.assertEqual(summary["claim_ready_count"], 2)
        self.assertEqual(summary["review_required_count"], 1)
        self.assertEqual(summary["blocked_count"], 1)
        self.assertEqual(summary["verified_claim_ready_recovery"], "1260000.00")
        self.assertEqual(summary["review_required_pipeline"], "187500.00")
        self.assertEqual(summary["blocked_potential"], "200000.00")
        self.assertEqual(summary["total_identified_before_status_filter"], "1647500.00")

        statuses = {item["claim_id"]: item["status"] for item in evaluated["results"]}
        self.assertEqual(statuses["TAP-DEMO-C-001"], "claim_ready")
        self.assertEqual(statuses["TAP-DEMO-C-002"], "claim_ready")
        self.assertEqual(statuses["TAP-DEMO-C-003"], "blocked")
        self.assertEqual(statuses["TAP-DEMO-C-004"], "review_required")

        blocked = next(item for item in evaluated["results"] if item["claim_id"] == "TAP-DEMO-C-003")
        self.assertIn("missing_evidence:workscope", blocked["blocking_issues"])
        self.assertIn("missing_evidence:payment_proof", blocked["blocking_issues"])

        review = next(item for item in evaluated["results"] if item["claim_id"] == "TAP-DEMO-C-004")
        self.assertIn("deadline_approaching:24_days", review["warnings"])


if __name__ == "__main__":
    unittest.main()
