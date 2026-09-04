import json
import unittest

from operator_app import UI_ROOT, build_evaluation_response, load_synthetic_example


class OperatorAppTests(unittest.TestCase):
    def test_synthetic_example_evaluates_without_inflating_recovery(self):
        payload = load_synthetic_example()
        response = build_evaluation_response(payload)

        evaluation = response["evaluation"]
        summary = evaluation["summary"]

        self.assertEqual(summary["currency"], "USD")
        self.assertEqual(summary["candidate_count"], 3)
        self.assertEqual(summary["claim_ready_count"], 2)
        self.assertEqual(summary["blocked_count"], 1)
        self.assertIn("not recovered cash", response["truth_note"])
        self.assertIn("**Verified settled recovery:** USD 0.00", response["executive_report_markdown"])

    def test_operator_ui_assets_exist_and_keep_assisted_boundary_visible(self):
        index = (UI_ROOT / "index.html").read_text(encoding="utf-8")
        css = (UI_ROOT / "app.css").read_text(encoding="utf-8")
        js = (UI_ROOT / "app.js").read_text(encoding="utf-8")

        self.assertIn("AERVIND", index)
        self.assertIn("Assisted operator workspace", index)
        self.assertIn("Local processing · no server persistence", index)
        self.assertIn("Human release gate required before externalization", index)
        self.assertIn("/api/evaluate", js)
        self.assertIn("status-claim_ready", css)

    def test_evaluation_response_is_json_serializable(self):
        response = build_evaluation_response(load_synthetic_example())
        rendered = json.dumps(response)
        self.assertIn("executive_report_markdown", rendered)

    def test_ui_does_not_embed_customer_payloads(self):
        for name in ("index.html", "app.css", "app.js"):
            text = (UI_ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("SyntheticLease001.pdf", text)
            self.assertNotIn("SYNTH-C-001", text)


if __name__ == "__main__":
    unittest.main()
