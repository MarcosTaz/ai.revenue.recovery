import json
import unittest
from datetime import datetime
from pathlib import Path

from govmargin.authz import AuthorizationError, OrganizationMember, Role
from govmargin.review import HumanReview, ReviewDecision
from govmargin.secure_operation import ReviewAuthorizationError, run_authorized_normalized_indirect_audit


class SecureOperationTests(unittest.TestCase):
    def setUp(self):
        self.memberships = (
            OrganizationMember("synthetic-org", "analyst-1", Role.ANALYST),
            OrganizationMember("synthetic-org", "reviewer-1", Role.REVIEWER),
            OrganizationMember("org-b", "analyst-2", Role.ANALYST),
            OrganizationMember("org-b", "reviewer-2", Role.REVIEWER),
        )
        fixture = Path(__file__).resolve().parents[1] / "examples" / "normalized-indirect-bundle.json"
        self.bundle = json.loads(fixture.read_text(encoding="utf-8"))

    def review(self, reviewer_id="reviewer-1", reviewer_role="REVIEWER"):
        return HumanReview(
            finding_id=self.bundle["finding_id"],
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            decision=ReviewDecision.APPROVED,
            rationale="Evidence and deterministic calculation reviewed.",
            reviewed_at=datetime.fromisoformat("2026-08-29T18:00:00+00:00"),
        )

    def test_authorized_analyst_can_run_audit(self):
        result = run_authorized_normalized_indirect_audit(
            self.bundle,
            actor_user_id="analyst-1",
            memberships=self.memberships,
        )
        self.assertEqual(result.pack.status.value, "DRAFT")

    def test_cross_tenant_analyst_cannot_run_audit(self):
        with self.assertRaises(AuthorizationError):
            run_authorized_normalized_indirect_audit(
                self.bundle,
                actor_user_id="analyst-2",
                memberships=self.memberships,
            )

    def test_authorized_reviewer_can_promote_pack(self):
        result = run_authorized_normalized_indirect_audit(
            self.bundle,
            actor_user_id="analyst-1",
            memberships=self.memberships,
            reviews=(self.review(),),
        )
        self.assertEqual(result.pack.status.value, "READY_FOR_CLIENT_FINANCE_REVIEW")

    def test_cross_tenant_reviewer_cannot_approve(self):
        with self.assertRaises(ReviewAuthorizationError):
            run_authorized_normalized_indirect_audit(
                self.bundle,
                actor_user_id="analyst-1",
                memberships=self.memberships,
                reviews=(self.review("reviewer-2"),),
            )

    def test_forged_reviewer_role_cannot_approve(self):
        with self.assertRaises(ReviewAuthorizationError):
            run_authorized_normalized_indirect_audit(
                self.bundle,
                actor_user_id="analyst-1",
                memberships=self.memberships,
                reviews=(self.review("reviewer-1", "ADMIN"),),
            )

    def test_analyst_cannot_self_approve_by_signing_reviewer_role(self):
        with self.assertRaises(ReviewAuthorizationError):
            run_authorized_normalized_indirect_audit(
                self.bundle,
                actor_user_id="analyst-1",
                memberships=self.memberships,
                reviews=(self.review("analyst-1", "REVIEWER"),),
            )


if __name__ == "__main__":
    unittest.main()
