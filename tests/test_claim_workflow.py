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
    allowed_transitions,
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
                external_reference="PORTAL-1",
            )

    def test_submission_requires_external_reference(self):
        record = self._record(ClaimLifecycle.CLAIM_READY)
        with self.assertRaisesRegex(WorkflowError, "external evidence/reference"):
            transition_claim(
                record,
                ClaimLifecycle.SUBMITTED,
                occurred_at=NOW,
                actor="claims@example.com",
                reason="real submission occurred",
            )

        updated, event = transition_claim(
            record,
            ClaimLifecycle.SUBMITTED,
            occurred_at=NOW,
            actor="claims@example.com",
            reason="real submission occurred",
            external_reference="LESSOR-PORTAL-123",
        )
        self.assertEqual(updated.lifecycle, ClaimLifecycle.SUBMITTED)
        self.assertEqual(event.external_reference, "LESSOR-PORTAL-123")

    def test_external_counterparty_state_requires_reference(self):
        record = self._record(ClaimLifecycle.SUBMITTED)
        with self.assertRaisesRegex(WorkflowError, "external evidence/reference"):
            transition_claim(
                record,
                ClaimLifecycle.APPROVED,
                occurred_at=NOW,
                actor="claims@example.com",
                reason="lessor approved",
            )

        updated, event = transition_claim(
            record,
            ClaimLifecycle.APPROVED,
            occurred_at=NOW,
            actor="claims@example.com",
            reason="lessor approved",
            external_reference="LESSOR-APPROVAL-456",
        )
        self.assertEqual(updated.lifecycle, ClaimLifecycle.APPROVED)
        self.assertEqual(event.external_reference, "LESSOR-APPROVAL-456")

    def test_internal_rejection_from_review_does_not_fake_external_reference(self):
        updated, event = transition_claim(
            self._record(ClaimLifecycle.REVIEWING),
            ClaimLifecycle.REJECTED,
            occurred_at=NOW,
            actor="reviewer@example.com",
            reason="candidate disproved internally",
        )
        self.assertEqual(updated.lifecycle, ClaimLifecycle.REJECTED)
        self.assertIsNone(event.external_reference)

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

    def test_settlement_cannot_exceed_asserted_amount(self):
        record = self._record(ClaimLifecycle.APPROVED)
        evidence = SettlementEvidence(
            settlement_type=SettlementType.CASH_RECEIPT,
            amount=Decimal("900001"),
            currency="USD",
            reference="BANK-OVER",
        )
        with self.assertRaisesRegex(WorkflowError, "exceeds asserted"):
            transition_claim(
                record,
                ClaimLifecycle.SETTLED,
                occurred_at=NOW,
                actor="finance@example.com",
                reason="cash received",
                settlement_evidence=evidence,
            )

    def test_unsettled_record_cannot_contain_settlement_value(self):
        record = ClaimRecord(
            claim_id="C-001",
            lifecycle=ClaimLifecycle.APPROVED,
            currency="USD",
            asserted_recovery_amount=Decimal("900000"),
            verified_settled_amount=Decimal("1"),
        )
        with self.assertRaisesRegex(WorkflowError, "unsettled"):
            transition_claim(
                record,
                ClaimLifecycle.SETTLED,
                occurred_at=NOW,
                actor="finance@example.com",
                reason="cash received",
                settlement_evidence=SettlementEvidence(
                    settlement_type=SettlementType.CASH_RECEIPT,
                    amount=Decimal("900000"),
                    currency="USD",
                    reference="BANK-001",
                ),
            )

    def test_settlement_evidence_rejected_on_non_settlement_transition(self):
        with self.assertRaisesRegex(WorkflowError, "only for a settled transition"):
            transition_claim(
                self._record(ClaimLifecycle.SUBMITTED),
                ClaimLifecycle.APPROVED,
                occurred_at=NOW,
                actor="claims@example.com",
                reason="approved",
                external_reference="LESSOR-APPROVAL-1",
                settlement_evidence=SettlementEvidence(
                    settlement_type=SettlementType.CASH_RECEIPT,
                    amount=Decimal("10"),
                    currency="USD",
                    reference="BANK-001",
                ),
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

    def test_allowed_transitions_are_exposed_without_mutating_graph(self):
        self.assertEqual(
            set(allowed_transitions(ClaimLifecycle.APPROVED)),
            {ClaimLifecycle.SETTLED},
        )
        self.assertEqual(allowed_transitions(ClaimLifecycle.SETTLED), ())


if __name__ == "__main__":
    unittest.main()
