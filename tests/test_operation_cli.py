from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from govmargin.engine import FindingState
from govmargin.operation import AuditBundleError, run_normalized_indirect_audit
from govmargin.pack import PackStatus
from govmargin.review import HumanReview, ReviewDecision

D = Decimal
HASH = hashlib.sha256(b"rate").hexdigest()


def bundle(**overrides):
    data = {
        "organization_id": "org-a",
        "contract_id": "C1",
        "period": "FY2025",
        "finding_id": "F1",
        "allocation_base": "1000",
        "final_rate": "0.20",
        "billed_indirect": "150",
        "rate_state": "SETTLED_FINAL",
        "contract_terms": "SUPPORTED",
        "base_allowability": "SUPPORTED",
        "base_allocability": "SUPPORTED",
        "remaining_funding": "500",
        "rule_ids": ["FAR_52_216_7_D2V_UPDATE_BILLINGS"],
        "evidence": [{
            "evidence_id": "e1",
            "source_type": "rate_agreement",
            "source_locator": "file://rate.pdf",
            "sha256": HASH,
            "observed_at": "2026-08-29T02:00:00+00:00",
        }],
        "assumptions": [],
    }
    data.update(overrides)
    return data


class OperationTests(unittest.TestCase):
    def test_realistic_normalized_bundle_produces_draft_candidate(self):
        result = run_normalized_indirect_audit(bundle())
        self.assertEqual(result.finding.state, FindingState.RECOVERY_CANDIDATE)
        self.assertEqual(result.finding.variance, D("50.00"))
        self.assertEqual(result.pack.status, PackStatus.DRAFT)

    def test_approved_review_promotes_pack_not_calculation(self):
        review = HumanReview("F1", "reviewer-1", "GovCon finance reviewer", ReviewDecision.APPROVED, "Source evidence and rule lineage checked.", datetime.now(timezone.utc))
        result = run_normalized_indirect_audit(bundle(), [review])
        self.assertEqual(result.pack.status, PackStatus.READY_FOR_CLIENT_FINANCE_REVIEW)
        self.assertEqual(result.finding.variance, D("50.00"))

    def test_unknown_rule_id_is_rejected(self):
        with self.assertRaises(AuditBundleError):
            run_normalized_indirect_audit(bundle(rule_ids=["INVENTED_RULE"]))

    def test_invalid_hash_is_rejected(self):
        bad = bundle()
        bad["evidence"] = [{**bad["evidence"][0], "sha256": "bad"}]
        with self.assertRaises(ValueError):
            run_normalized_indirect_audit(bad)

    def test_overbilling_remains_payable(self):
        result = run_normalized_indirect_audit(bundle(billed_indirect="250"))
        self.assertEqual(result.finding.state, FindingState.PAYABLE_CANDIDATE)
        self.assertEqual(result.pack.status, PackStatus.NO_RECOVERY_PACK)
        self.assertEqual(len(result.pack.payable_exposures), 1)


class CliTests(unittest.TestCase):
    def test_example_bundle_runs_from_cli(self):
        repo = Path(__file__).resolve().parents[1]
        process = subprocess.run(
            [sys.executable, "-m", "govmargin.cli", str(repo / "examples" / "normalized-indirect-bundle.json")],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        payload = json.loads(process.stdout)
        self.assertEqual(payload["finding"]["state"], "RECOVERY_CANDIDATE")
        self.assertEqual(payload["pack_status"], "DRAFT")


if __name__ == "__main__":
    unittest.main()
