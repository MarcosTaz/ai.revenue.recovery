import json
import unittest
from pathlib import Path

from aviation_io import evaluate_payload


class AviationIOTests(unittest.TestCase):
    def test_synthetic_pilot_pipeline(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        evaluated = evaluate_payload(payload)

        self.assertEqual(evaluated["summary"]["currency"], "USD")
        self.assertEqual(evaluated["summary"]["candidate_count"], 3)
        self.assertEqual(evaluated["summary"]["claim_ready_count"], 2)
        self.assertEqual(evaluated["summary"]["blocked_count"], 1)
        self.assertEqual(
            evaluated["summary"]["verified_claim_ready_recovery"], "1125000.00"
        )
        self.assertEqual(evaluated["summary"]["blocked_potential"], "220000.00")
        self.assertEqual(
            evaluated["summary"]["total_identified_before_status_filter"], "1345000.00"
        )

        by_id = {item["claim_id"]: item for item in evaluated["results"]}
        self.assertEqual(by_id["SYNTH-C-001"]["net_recoverable"], "900000.00")
        self.assertEqual(by_id["SYNTH-C-002"]["net_recoverable"], "225000.00")
        self.assertIn("missing_evidence:workscope", by_id["SYNTH-C-003"]["blocking_issues"])

        dossier_by_id = {
            item["claim"]["claim_id"]: item for item in evaluated["dossiers"]
        }
        self.assertEqual(dossier_by_id["SYNTH-C-001"]["lineage_gaps"], [])
        self.assertEqual(dossier_by_id["SYNTH-C-002"]["lineage_gaps"], [])

    def test_duplicate_claim_ids_are_rejected(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["claims"].append(dict(payload["claims"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate claim_id"):
            evaluate_payload(payload)


if __name__ == "__main__":
    unittest.main()
