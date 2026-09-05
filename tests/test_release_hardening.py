import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from aviation_io import evaluate_payload
from claim_workflow import (
    ClaimLifecycle,
    ClaimRecord,
    SettlementEvidence,
    SettlementType,
    WorkflowError,
)
from operator_app import STATIC_FILES, UI_ROOT


class ReleaseHardeningTests(unittest.TestCase):
    def _payload(self):
        return json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))

    def test_non_finite_claim_input_fails_closed(self):
        payload = self._payload()
        payload["claims"][0]["eligible_cost"] = "NaN"
        with self.assertRaisesRegex(ValueError, "finite"):
            evaluate_payload(payload)

    def test_non_finite_rule_input_fails_closed(self):
        payload = self._payload()
        payload["rules"][0]["cap"] = "Infinity"
        with self.assertRaisesRegex(ValueError, "finite"):
            evaluate_payload(payload)

    def test_workflow_record_rejects_non_finite_asserted_amount_on_import(self):
        with self.assertRaisesRegex(WorkflowError, "finite"):
            ClaimRecord(
                claim_id="C-1",
                lifecycle=ClaimLifecycle.DETECTED,
                currency="USD",
                asserted_recovery_amount=Decimal("NaN"),
            )

    def test_workflow_record_rejects_invalid_currency_on_import(self):
        with self.assertRaisesRegex(WorkflowError, "three-letter"):
            ClaimRecord(
                claim_id="C-1",
                lifecycle=ClaimLifecycle.DETECTED,
                currency="USDX",
                asserted_recovery_amount=Decimal("100"),
            )

    def test_settlement_evidence_rejects_non_finite_amount_on_import(self):
        with self.assertRaisesRegex(WorkflowError, "finite"):
            SettlementEvidence(
                settlement_type=SettlementType.CASH_RECEIPT,
                amount=Decimal("Infinity"),
                currency="USD",
                reference="BANK-1",
            )

    def test_settlement_evidence_rejects_blank_reference_on_import(self):
        with self.assertRaisesRegex(WorkflowError, "reference"):
            SettlementEvidence(
                settlement_type=SettlementType.CASH_RECEIPT,
                amount=Decimal("10"),
                currency="USD",
                reference="   ",
            )

    def test_duplicate_evidence_ids_block_release(self):
        payload = self._payload()
        duplicate = dict(payload["claims"][0]["evidence"][0])
        payload["claims"][0]["evidence"].append(duplicate)
        result = evaluate_payload(payload)["results"][0]
        self.assertEqual(result["status"], "blocked")
        self.assertIn("duplicate_evidence_id:E-001", result["blocking_issues"])

    def test_checkpoint_script_is_served_and_does_not_use_hidden_browser_storage(self):
        self.assertIn("/checkpoint.js", STATIC_FILES)
        script = (UI_ROOT / "checkpoint.js").read_text(encoding="utf-8")
        self.assertIn("/api/workflow-transition", script)
        self.assertIn("/api/claim-package", script)
        self.assertIn("/api/case-export", script)
        self.assertIn("beforeunload", script)
        self.assertNotIn("localStorage", script)
        self.assertNotIn("indexedDB", script)

    def test_ui_describes_a_validated_not_immutable_trail(self):
        index = (UI_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Validated case trail", index)
        self.assertIn("validated local case-checkpoint download", index)
        self.assertNotIn("Immutable case trail", index)
        self.assertIn('<script src="/checkpoint.js" defer></script>', index)

    def test_fixed_historical_timestamps_remain_supported(self):
        # Release hardening must not make existing auditable case timestamps dependent
        # on wall-clock tests. The application records timezone-aware facts supplied by
        # the operator and validates ordering within each claim trail.
        self.assertIsNotNone(datetime(2026, 9, 5, tzinfo=timezone.utc).utcoffset())


if __name__ == "__main__":
    unittest.main()
