import unittest
from decimal import Decimal

from aviation_recovery import EvaluationResult, Status, summarize_recovery


class SummaryTruthTests(unittest.TestCase):
    def test_blocked_value_is_not_counted_as_net_recoverable(self):
        ready = EvaluationResult(
            claim_id="READY",
            rule_id="R1",
            status=Status.CLAIM_READY,
            currency="USD",
            gross_entitlement=Decimal("100000"),
            net_recoverable=Decimal("100000"),
            blocking_issues=(),
            warnings=(),
            calculation_trace=(),
            evidence_ids=(),
        )
        blocked = EvaluationResult(
            claim_id="BLOCKED",
            rule_id="R2",
            status=Status.BLOCKED,
            currency="USD",
            gross_entitlement=Decimal("250000"),
            net_recoverable=Decimal("250000"),
            blocking_issues=("missing_evidence:workscope",),
            warnings=(),
            calculation_trace=(),
            evidence_ids=(),
        )
        summary = summarize_recovery([ready, blocked])
        self.assertEqual(summary["net_recoverable"], Decimal("100000.00"))
        self.assertEqual(summary["blocked_potential"], Decimal("250000.00"))
        self.assertEqual(
            summary["total_identified_before_status_filter"], Decimal("350000.00")
        )


if __name__ == "__main__":
    unittest.main()
