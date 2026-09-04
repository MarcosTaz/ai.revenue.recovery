from datetime import datetime, timezone
from decimal import Decimal
import unittest

from govmargin.domain import EconomicFinding, EvidenceRef, RateAgreement
from govmargin.engine import FindingState
from govmargin.portfolio import summarize_findings

D = Decimal
EVID = ("e1",)
RULE = ("r1",)


class DomainTests(unittest.TestCase):
    def test_evidence_requires_sha256(self):
        with self.assertRaises(ValueError):
            EvidenceRef("e1", "invoice", "I-1", "bad", datetime.now(timezone.utc))

    def test_settled_rate_requires_date(self):
        with self.assertRaises(ValueError):
            RateAgreement("ra1", "c1", 2025, True, None, EVID)

    def test_candidate_requires_evidence(self):
        with self.assertRaises(ValueError):
            EconomicFinding(
                "f1",
                "c1",
                FindingState.RECOVERY_CANDIDATE,
                D("100"),
                D("0"),
                None,
                D("100"),
                (),
                RULE,
            )


class PortfolioTests(unittest.TestCase):
    def finding(self, fid, state, variance):
        return EconomicFinding(
            fid,
            "c1",
            state,
            D("100") if variance is not None else None,
            D("0") if variance is not None else None,
            None,
            variance,
            EVID if state in {FindingState.RECOVERY_CANDIDATE, FindingState.PAYABLE_CANDIDATE} else (),
            RULE if state in {FindingState.RECOVERY_CANDIDATE, FindingState.PAYABLE_CANDIDATE} else (),
        )

    def test_summary_does_not_net_receivable_and_payable(self):
        summary = summarize_findings(
            [
                self.finding("r", FindingState.RECOVERY_CANDIDATE, D("1000")),
                self.finding("p", FindingState.PAYABLE_CANDIDATE, D("-400")),
                self.finding("u", FindingState.UNKNOWN, None),
                self.finding("x", FindingState.REQUIRES_REVIEW, None),
            ]
        )
        self.assertEqual(summary.recovery_candidates, D("1000.00"))
        self.assertEqual(summary.payable_candidates, D("400.00"))
        self.assertEqual(summary.unknown_count, 1)
        self.assertEqual(summary.review_count, 1)
        self.assertEqual(summary.finding_count, 4)

    def test_invalid_positive_payable_is_rejected(self):
        bad = self.finding("p", FindingState.PAYABLE_CANDIDATE, D("50"))
        with self.assertRaises(ValueError):
            summarize_findings([bad])


if __name__ == "__main__":
    unittest.main()
