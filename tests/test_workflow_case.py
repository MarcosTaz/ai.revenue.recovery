import copy
import json
import unittest
from pathlib import Path

from aviation_io import evaluate_payload
from workflow_case import (
    CASE_SCHEMA_VERSION,
    build_case_export,
    cohort_digest,
    parse_bundle,
    record_claim_package_artifact,
    transition_bundle,
    workflow_view,
)


NOW_1 = "2026-09-04T15:00:00+00:00"
NOW_2 = "2026-09-04T15:01:00+00:00"
NOW_3 = "2026-09-04T15:02:00+00:00"
NOW_4 = "2026-09-04T15:03:00+00:00"
NOW_5 = "2026-09-04T15:04:00+00:00"


class WorkflowCaseTests(unittest.TestCase):
    def setUp(self):
        self.cohort = json.loads(Path("examples/pilot.json").read_text(encoding="utf-8"))
        self.evaluated = evaluate_payload(self.cohort)
        self.claim_id = "SYNTH-C-001"

    def _to_reviewing(self):
        return transition_bundle(
            cohort=self.cohort,
            evaluated=self.evaluated,
            bundle=None,
            claim_id=self.claim_id,
            target="reviewing",
            occurred_at=NOW_1,
            actor="operator@aervind.com",
            reason="opened human review",
        )

    def _to_claim_ready(self):
        reviewing = self._to_reviewing()
        return transition_bundle(
            cohort=self.cohort,
            evaluated=self.evaluated,
            bundle=reviewing,
            claim_id=self.claim_id,
            target="claim_ready",
            occurred_at=NOW_2,
            actor="reviewer@aervind.com",
            reason="economic and lineage review passed",
        )

    def test_full_external_lifecycle_is_auditable(self):
        bundle = self._to_claim_ready()
        bundle = transition_bundle(
            cohort=self.cohort,
            evaluated=self.evaluated,
            bundle=bundle,
            claim_id=self.claim_id,
            target="submitted",
            occurred_at=NOW_3,
            actor="operator@aervind.com",
            reason="submitted through lessor channel",
            external_reference="LESSOR-PORTAL-123",
        )
        bundle = transition_bundle(
            cohort=self.cohort,
            evaluated=self.evaluated,
            bundle=bundle,
            claim_id=self.claim_id,
            target="approved",
            occurred_at=NOW_4,
            actor="operator@aervind.com",
            reason="lessor approval received",
            external_reference="LESSOR-APPROVAL-456",
        )
        bundle = transition_bundle(
            cohort=self.cohort,
            evaluated=self.evaluated,
            bundle=bundle,
            claim_id=self.claim_id,
            target="settled",
            occurred_at=NOW_5,
            actor="finance@aervind.com",
            reason="credit memo reconciled",
            settlement={
                "settlement_type": "credit_memo",
                "amount": "875000",
                "currency": "USD",
                "reference": "CM-7781",
            },
        )
        view = workflow_view(bundle)
        record = view["records"][0]
        self.assertEqual(view["schema_version"], CASE_SCHEMA_VERSION)
        self.assertEqual(record["lifecycle"], "settled")
        self.assertEqual(record["verified_settled_amount"], "875000")
        self.assertEqual(record["allowed_transitions"], [])
        self.assertEqual(record["audit_event_count"], 5)
        self.assertEqual(view["events"][2]["external_reference"], "LESSOR-PORTAL-123")
        self.assertEqual(view["events"][-1]["settlement_reference"], "CM-7781")

    def test_submission_requires_external_reference(self):
        bundle = self._to_claim_ready()
        with self.assertRaisesRegex(ValueError, "external evidence/reference"):
            transition_bundle(
                cohort=self.cohort,
                evaluated=self.evaluated,
                bundle=bundle,
                claim_id=self.claim_id,
                target="submitted",
                occurred_at=NOW_3,
                actor="operator@aervind.com",
                reason="submitted",
            )

    def test_released_workflow_is_bound_to_cohort_revision(self):
        bundle = self._to_claim_ready()
        changed = copy.deepcopy(self.cohort)
        changed["claims"][0]["source_refs"]["eligible_cost"] = "RevisedSource.xlsx#v2"
        changed_eval = evaluate_payload(changed)
        with self.assertRaisesRegex(ValueError, "cohort changed after"):
            transition_bundle(
                cohort=changed,
                evaluated=changed_eval,
                bundle=bundle,
                claim_id=self.claim_id,
                target="submitted",
                occurred_at=NOW_3,
                actor="operator@aervind.com",
                reason="submit revised data without new review revision",
                external_reference="REF-1",
            )

    def test_released_workflow_without_digest_is_rejected(self):
        bundle = self._to_claim_ready()
        del bundle["cohort_digest"]
        with self.assertRaisesRegex(ValueError, "missing its bound cohort digest"):
            transition_bundle(
                cohort=self.cohort,
                evaluated=self.evaluated,
                bundle=bundle,
                claim_id=self.claim_id,
                target="submitted",
                occurred_at=NOW_3,
                actor="operator@aervind.com",
                reason="submit",
                external_reference="REF-1",
            )

    def test_pre_release_review_can_rebind_to_updated_cohort(self):
        bundle = self._to_reviewing()
        changed = copy.deepcopy(self.cohort)
        changed["claims"][0]["source_refs"]["eligible_cost"] = "RevisedSource.xlsx#v2"
        changed_eval = evaluate_payload(changed)
        rebound = transition_bundle(
            cohort=changed,
            evaluated=changed_eval,
            bundle=bundle,
            claim_id=self.claim_id,
            target="claim_ready",
            occurred_at=NOW_2,
            actor="reviewer@aervind.com",
            reason="reviewed revised source set",
        )
        self.assertEqual(rebound["cohort_digest"], cohort_digest(changed))

    def test_claim_package_artifact_is_hashed_and_never_submitted(self):
        bundle = self._to_claim_ready()
        updated = record_claim_package_artifact(
            cohort=self.cohort,
            evaluated=self.evaluated,
            bundle=bundle,
            claim_id=self.claim_id,
            generated_at=NOW_3,
            generated_by="operator@aervind.com",
            content="# claim package\namount: 900000",
        )
        artifact = updated["artifacts"][0]
        self.assertEqual(artifact["kind"], "claim_package")
        self.assertEqual(artifact["submission_status"], "not_submitted")
        self.assertEqual(len(artifact["content_sha256"]), 64)

    def test_artifact_outside_claim_ready_window_is_rejected(self):
        bundle = self._to_claim_ready()
        bundle = transition_bundle(
            cohort=self.cohort,
            evaluated=self.evaluated,
            bundle=bundle,
            claim_id=self.claim_id,
            target="submitted",
            occurred_at=NOW_3,
            actor="operator@aervind.com",
            reason="submitted",
            external_reference="PORTAL-123",
        )
        bundle["artifacts"] = [
            {
                "claim_id": self.claim_id,
                "kind": "claim_package",
                "generated_at": NOW_4,
                "generated_by": "operator@aervind.com",
                "content_sha256": "a" * 64,
                "submission_status": "not_submitted",
            }
        ]
        with self.assertRaisesRegex(ValueError, "while lifecycle is claim_ready"):
            parse_bundle(bundle)

    def test_fabricated_submitted_event_without_reference_is_rejected(self):
        bundle = self._to_claim_ready()
        bundle["records"][0]["lifecycle"] = "submitted"
        bundle["events"].append(
            {
                "claim_id": self.claim_id,
                "from_state": "claim_ready",
                "to_state": "submitted",
                "occurred_at": NOW_3,
                "actor": "operator@aervind.com",
                "reason": "fabricated missing reference",
                "external_reference": None,
                "settlement_reference": None,
            }
        )
        with self.assertRaisesRegex(ValueError, "requires external reference"):
            parse_bundle(bundle)

    def test_fabricated_non_detected_record_without_audit_trail_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "without audit trail"):
            parse_bundle(
                {
                    "schema_version": CASE_SCHEMA_VERSION,
                    "records": [
                        {
                            "claim_id": self.claim_id,
                            "lifecycle": "approved",
                            "currency": "USD",
                            "asserted_recovery_amount": "900000",
                            "verified_settled_amount": "0",
                        }
                    ],
                    "events": [],
                    "artifacts": [],
                }
            )

    def test_old_schema_is_rejected_instead_of_silently_migrated(self):
        with self.assertRaisesRegex(ValueError, "unsupported workflow schema_version"):
            parse_bundle({"schema_version": 1, "records": [], "events": [], "artifacts": []})

    def test_unversioned_workflow_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "schema_version is required"):
            parse_bundle({"records": [], "events": [], "artifacts": []})

    def test_case_export_preserves_cohort_workflow_and_digest(self):
        bundle = self._to_reviewing()
        exported = build_case_export(
            cohort=self.cohort,
            evaluated=self.evaluated,
            workflow_bundle=bundle,
        )
        self.assertEqual(exported["schema_version"], CASE_SCHEMA_VERSION)
        self.assertEqual(exported["kind"], "aervind_assisted_case")
        self.assertEqual(exported["workflow"]["cohort_digest"], cohort_digest(self.cohort))
        self.assertEqual(exported["cohort"]["claims"][0]["claim_id"], self.claim_id)


if __name__ == "__main__":
    unittest.main()
