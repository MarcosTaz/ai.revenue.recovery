import json
import unittest

from operator_app import (
    UI_ROOT,
    build_case_export_response,
    build_case_response,
    build_claim_package_response,
    build_evaluation_response,
    build_workflow_transition_response,
    load_synthetic_example,
)


class OperatorAppTests(unittest.TestCase):
    def _claim_ready_workflow(self):
        payload = load_synthetic_example()
        first = build_workflow_transition_response(
            cohort=payload,
            workflow_bundle=None,
            claim_id="SYNTH-C-001",
            target="reviewing",
            occurred_at="2026-09-04T15:00:00+00:00",
            actor="operator@aervind.com",
            reason="opened review",
        )
        second = build_workflow_transition_response(
            cohort=payload,
            workflow_bundle=first["workflow"],
            claim_id="SYNTH-C-001",
            target="claim_ready",
            occurred_at="2026-09-04T15:01:00+00:00",
            actor="reviewer@aervind.com",
            reason="economic and source review passed",
        )
        return payload, second["workflow"]

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
        self.assertEqual(response["management_truth"]["claim_ready_not_submitted"], "1125000.00")
        self.assertEqual(response["management_truth"]["verified_settled_recovery"], "0")
        self.assertTrue(response["workflow"]["cohort_digest"])

    def test_claim_ready_candidate_generates_audited_package_but_never_submits(self):
        payload, workflow = self._claim_ready_workflow()
        response = build_claim_package_response(
            payload,
            workflow_bundle=workflow,
            claim_id="SYNTH-C-001",
            human_release_confirmed=True,
            generated_at="2026-09-04T15:02:00+00:00",
            generated_by="reviewer@aervind.com",
        )

        self.assertEqual(response["claim_id"], "SYNTH-C-001")
        self.assertTrue(response["human_release_confirmed"])
        self.assertEqual(response["submission_status"], "not_submitted")
        self.assertIn(
            "# Aviation Lease Entitlement Claim Package",
            response["claim_package_markdown"],
        )
        self.assertEqual(response["external_dossier"]["externalization_gate"], "passed")
        self.assertIn("does not send or submit", response["submission_note"])
        artifacts = response["workflow_view"]["artifacts"]
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0]["submission_status"], "not_submitted")
        self.assertEqual(len(artifacts[0]["content_sha256"]), 64)

    def test_claim_package_requires_explicit_human_release(self):
        payload, workflow = self._claim_ready_workflow()
        with self.assertRaisesRegex(ValueError, "human release confirmation is required"):
            build_claim_package_response(
                payload,
                workflow_bundle=workflow,
                claim_id="SYNTH-C-001",
                human_release_confirmed=False,
                generated_at="2026-09-04T15:02:00+00:00",
                generated_by="reviewer@aervind.com",
            )

    def test_claim_package_requires_auditable_claim_ready_workflow_state(self):
        payload = load_synthetic_example()
        response = build_case_response(payload)
        with self.assertRaisesRegex(ValueError, "workflow lifecycle"):
            build_claim_package_response(
                payload,
                workflow_bundle=response["workflow"],
                claim_id="SYNTH-C-001",
                human_release_confirmed=True,
                generated_at="2026-09-04T15:02:00+00:00",
                generated_by="reviewer@aervind.com",
            )

    def test_blocked_candidate_cannot_reach_claim_ready(self):
        payload = load_synthetic_example()
        reviewing = build_workflow_transition_response(
            cohort=payload,
            workflow_bundle=None,
            claim_id="SYNTH-C-003",
            target="reviewing",
            occurred_at="2026-09-04T15:00:00+00:00",
            actor="operator@aervind.com",
            reason="opened review",
        )
        with self.assertRaisesRegex(ValueError, "claim-ready economic evaluation"):
            build_workflow_transition_response(
                cohort=payload,
                workflow_bundle=reviewing["workflow"],
                claim_id="SYNTH-C-003",
                target="claim_ready",
                occurred_at="2026-09-04T15:01:00+00:00",
                actor="reviewer@aervind.com",
                reason="attempt release",
            )

    def test_submitted_state_moves_value_out_of_claim_ready_bucket(self):
        payload, workflow = self._claim_ready_workflow()
        submitted = build_workflow_transition_response(
            cohort=payload,
            workflow_bundle=workflow,
            claim_id="SYNTH-C-001",
            target="submitted",
            occurred_at="2026-09-04T15:03:00+00:00",
            actor="operator@aervind.com",
            reason="real portal submission recorded",
            external_reference="PORTAL-123",
        )
        truth = submitted["management_truth"]
        self.assertEqual(truth["claim_ready_not_submitted"], "225000.00")
        self.assertEqual(truth["external_unsettled"], "900000.00")
        self.assertEqual(truth["verified_settled_recovery"], "0")
        self.assertIn("submitted", submitted["executive_report_markdown"])

    def test_portable_case_export_round_trips_workflow_state(self):
        payload, workflow = self._claim_ready_workflow()
        exported = build_case_export_response(payload, workflow)["case"]
        reopened = build_case_response(exported["cohort"], exported["workflow"])
        record = reopened["workflow_view"]["records"][0]
        self.assertEqual(exported["kind"], "aervind_assisted_case")
        self.assertEqual(record["lifecycle"], "claim_ready")
        self.assertEqual(record["audit_event_count"], 2)

    def test_operator_ui_assets_exist_and_keep_assisted_boundary_visible(self):
        index = (UI_ROOT / "index.html").read_text(encoding="utf-8")
        css = (UI_ROOT / "app.css").read_text(encoding="utf-8")
        js = (UI_ROOT / "app.js").read_text(encoding="utf-8")

        self.assertIn("AERVIND", index)
        self.assertIn("Assisted operator workspace", index)
        self.assertIn("No live airline-system access required", index)
        self.assertIn("Record what happened. Never simulate what happened.", index)
        self.assertIn("No claim is submitted by this console", index)
        self.assertIn("/api/evaluate-case", js)
        self.assertIn("/api/workflow-transition", js)
        self.assertIn("/api/claim-package", js)
        self.assertIn("/api/case-export", js)
        self.assertIn("human_release_confirmed", js)
        self.assertIn("submission_status !== 'not_submitted'", js)
        self.assertIn("status-claim_ready", css)
        self.assertIn("lifecycle-settled", css)
        self.assertIn("workflow-layout", css)

    def test_evaluation_response_is_json_serializable(self):
        response = build_evaluation_response(load_synthetic_example())
        rendered = json.dumps(response)
        self.assertIn("executive_report_markdown", rendered)
        self.assertIn("management_truth", rendered)
        self.assertIn("workflow_view", rendered)

    def test_ui_does_not_embed_customer_payloads(self):
        for name in ("index.html", "app.css", "app.js"):
            text = (UI_ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("SyntheticLease001.pdf", text)
            self.assertNotIn("SYNTH-C-001", text)


if __name__ == "__main__":
    unittest.main()
