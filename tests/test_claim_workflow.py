import unittest
from datetime import datetime, timezone
from decimal import Decimal

from aviation_recovery import Status
from claim_workflow import (
    ClaimLifecycle,
    ClaimRecord,
    SettlementEvidence,
    SettlementType,
    WorkflowError,
    transition_claim,
)


NOW = datetime(2026, 9, 4, 15, 0, tzinfo=timezone.utc)


class ClaimWorkflowTests(unittest.TestCase):
    def _record(self, lifecycle=ClaimLifecycle.REVIEWING):
        return ClaimRecord(
            claim_id="C-001",
            lifecycle=lifecycle,
            currency="USD",
            asserted_recovery_amount=Decimal("900000"),
        )

    def test_claim_ready_requires_economic_and_lineage_gates(self):
        record = self._record()
        with self.assertRaises(WorkflowError):
            transition_claim(
                record,
                ClaimLifecycle.CLAIM_READY,
                occurred_at=NOW,
                actor="reviewer@example.com",
                reason="review complete",
                evaluation_status=Status.BLOCKED,
                externalization_gate_passed=True,
            )

        with self.assertRaises(WorkflowError):
            transition_claim(
                record,
                ClaimLifecycle.CLAIM_READY,
                occurred_at=NOW,
                actor="reviewer@example.com",
                reason="review complete",
                evaluation_status=Status.CLAIM_READY,
                externalization_gate_passed=False,
            )

        updated, event = transition_claim(
            record,
            ClaimLifecycle.CLAIM_READY,
            occurred_at=NOW,
            actor="reviewer@example.com",
            reason="review complete",
            evaluation_status=Status.CLAIM_READY,
            externalization_gate_passed=True,
        )
        self.assertEqual(updated.lifecycle, ClaimLifecycle.CLAIM_READY)
        self.assertEqual(event.from_state, ClaimLifecycle.REVIEWING)

    def test_submitted_cannot_skip_claim_ready(self):
        with self.assertRaises(WorkflowError):
            transition_claim(
                self._record(),
                ClaimLifecycle.SUBMITTED,
                occurred_at=NOW,
                actor="claims@example.com",
                reason="submit claim",
            )

    def test_settled_requires_economic_evidence(self):
        record = self._record(ClaimLifecycle.APPROVED)
        with self.assertRaises(WorkflowError):
            transition_claim(
                record,
                ClaimLifecycle.SETTLED,
                occurred_at=NOW,
                actor="finance@example.com",
                reason="mark settled",
            )

    def test_settled_records_verified_amount(self):
        record = self._record(ClaimLifecycle.APPROVED)
        evidence = SettlementEvidence(
            settlement_type=SettlementType.CREDIT_MEMO,
            amount=Decimal("875000"),
            currency="USD",
            reference="CreditMemo-CM-7781",
        )
        updated, event = transition_claim(
            record,
            ClaimLifecycle.SETTLED,
            occurred_at=NOW,
            actor="finance@example.com",
            reason="credit memo received",
            settlement_evidence=evidence,
        )
        self.assertEqual(updated.lifecycle, ClaimLifecycle.SETTLED)
        self.assertEqual(updated.verified_settled_amount, Decimal("875000"))
        self.assertEqual(event.settlement_reference, "CreditMemo-CM-7781")

    def test_settlement_currency_mismatch_is_rejected(self):
        record = self._record(ClaimLifecycle.APPROVED)
        evidence = SettlementEvidence(
            settlement_type=SettlementType.CASH_RECEIPT,
            amount=Decimal("900000"),
            currency="EUR",
            reference="BANK-001",
        )
        with self.assertRaisesRegex(WorkflowError, "currency mismatch"):
            transition_claim(
                record,
                ClaimLifecycle.SETTLED,
                occurred_at=NOW,
                actor="finance@example.com",
                reason="cash received",
                settlement_evidence=evidence,
            )

    def test_rejected_claim_can_return_to_review(self):
        record = self._record(ClaimLifecycle.REJECTED)
        updated, _ = transition_claim(
            record,
            ClaimLifecycle.REVIEWING,
            occurred_at=NOW,
            actor="lease-team@example.com",
            reason="new evidence received",
        )
        self.assertEqual(updated.lifecycle, ClaimLifecycle.REVIEWING)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(WorkflowError, "timezone-aware"):
            transition_claim(
                self._record(ClaimLifecycle.DETECTED),
                ClaimLifecycle.REVIEWING,
                occurred_at=datetime(2026, 9, 4, 15, 0),
                actor="reviewer@example.com",
                reason="start review",
            )


if __name__ == "__main__":
    unittest.main()
