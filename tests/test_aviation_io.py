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

    def test_missing_lineage_cannot_inflate_claim_ready_summary(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["claims"][0]["source_refs"] = {}

        evaluated = evaluate_payload(payload)
        summary = evaluated["summary"]
        by_id = {item["claim_id"]: item for item in evaluated["results"]}
        dossier_by_id = {
            item["claim"]["claim_id"]: item for item in evaluated["dossiers"]
        }

        self.assertEqual(summary["claim_ready_count"], 1)
        self.assertEqual(summary["blocked_count"], 2)
        self.assertEqual(summary["verified_claim_ready_recovery"], "225000.00")
        self.assertEqual(summary["blocked_potential"], "1120000.00")
        self.assertEqual(by_id["SYNTH-C-001"]["status"], "blocked")
        self.assertIn(
            "missing_source_ref:rule_source",
            by_id["SYNTH-C-001"]["blocking_issues"],
        )
        self.assertEqual(dossier_by_id["SYNTH-C-001"]["claim"]["status"], "blocked")
        self.assertIn(
            "missing_source_ref:eligible_cost",
            dossier_by_id["SYNTH-C-001"]["lineage_gaps"],
        )

    def test_duplicate_claim_ids_are_rejected(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["claims"].append(dict(payload["claims"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate claim_id"):
            evaluate_payload(payload)

    def test_blank_claim_id_is_rejected_at_ingestion(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["claims"][0]["claim_id"] = "   "
        with self.assertRaisesRegex(ValueError, "claim_id is required"):
            evaluate_payload(payload)

    def test_unused_invalid_rule_is_still_rejected(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        invalid_rule = dict(payload["rules"][0])
        invalid_rule["rule_id"] = "UNUSED-BUT-INVALID"
        invalid_rule["effective_to"] = "2024-01-01"
        payload["rules"].append(invalid_rule)

        with self.assertRaisesRegex(ValueError, "effective_to cannot precede effective_from"):
            evaluate_payload(payload)

    def test_ids_and_currency_are_normalized_at_ingestion(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["rules"][0]["rule_id"] = "  SYNTH-LEASE-001-MR-ENGINE  "
        payload["rules"][0]["currency"] = " usd "
        payload["claims"][0]["rule_id"] = "  SYNTH-LEASE-001-MR-ENGINE  "
        payload["claims"][0]["claim_id"] = "  SYNTH-C-001  "

        evaluated = evaluate_payload(payload)
        by_id = {item["claim_id"]: item for item in evaluated["results"]}

        self.assertIn("SYNTH-C-001", by_id)
        self.assertEqual(by_id["SYNTH-C-001"]["currency"], "USD")

    def test_non_finite_financial_values_are_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
                payload["claims"][0]["eligible_cost"] = value
                with self.assertRaisesRegex(ValueError, "finite"):
                    evaluate_payload(payload)

    def test_non_finite_rule_values_are_rejected(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["rules"][0]["contribution_rate"] = "NaN"
        with self.assertRaisesRegex(ValueError, "finite"):
            evaluate_payload(payload)

    def test_invalid_currency_code_is_rejected(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["rules"][0]["currency"] = "USDX"
        with self.assertRaisesRegex(ValueError, "three-letter"):
            evaluate_payload(payload)

    def test_malformed_json_shapes_are_rejected_cleanly(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["claims"][0]["source_refs"] = ["not", "an", "object"]
        with self.assertRaisesRegex(ValueError, "source_refs must be a JSON object"):
            evaluate_payload(payload)

        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        payload["rules"][0]["required_evidence_types"] = "invoice"
        with self.assertRaisesRegex(ValueError, "required_evidence_types must be a JSON array"):
            evaluate_payload(payload)

    def test_duplicate_evidence_id_blocks_candidate(self):
        payload = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        duplicate = dict(payload["claims"][0]["evidence"][0])
        duplicate["evidence_type"] = "workscope"
        payload["claims"][0]["evidence"].append(duplicate)

        evaluated = evaluate_payload(payload)
        result = next(item for item in evaluated["results"] if item["claim_id"] == "SYNTH-C-001")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("duplicate_evidence_id:E-001", result["blocking_issues"])


if __name__ == "__main__":
    unittest.main()
