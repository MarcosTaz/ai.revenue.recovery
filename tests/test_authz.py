import unittest

from govmargin.authz import Action, AuthorizationError, OrganizationMember, Role, assert_same_organization, authorize


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.memberships = [
            OrganizationMember("org-a", "admin", Role.ADMIN),
            OrganizationMember("org-a", "analyst", Role.ANALYST),
            OrganizationMember("org-a", "reviewer", Role.REVIEWER),
            OrganizationMember("org-a", "viewer", Role.VIEWER),
            OrganizationMember("org-b", "analyst", Role.ANALYST),
        ]

    def test_analyst_can_import_and_run_but_not_review(self):
        self.assertEqual(authorize("org-a", "analyst", Action.IMPORT, self.memberships).role, Role.ANALYST)
        self.assertEqual(authorize("org-a", "analyst", Action.RUN_AUDIT, self.memberships).role, Role.ANALYST)
        with self.assertRaises(AuthorizationError):
            authorize("org-a", "analyst", Action.REVIEW_FINDING, self.memberships)

    def test_reviewer_can_review_but_not_import(self):
        self.assertEqual(authorize("org-a", "reviewer", Action.REVIEW_FINDING, self.memberships).role, Role.REVIEWER)
        with self.assertRaises(AuthorizationError):
            authorize("org-a", "reviewer", Action.IMPORT, self.memberships)

    def test_viewer_is_read_only(self):
        self.assertEqual(authorize("org-a", "viewer", Action.READ, self.memberships).role, Role.VIEWER)
        with self.assertRaises(AuthorizationError):
            authorize("org-a", "viewer", Action.RUN_AUDIT, self.memberships)

    def test_cross_tenant_membership_is_not_reused(self):
        with self.assertRaises(AuthorizationError):
            authorize("org-b", "reviewer", Action.READ, self.memberships)

    def test_inactive_member_is_denied(self):
        memberships = [OrganizationMember("org-a", "u", Role.ADMIN, active=False)]
        with self.assertRaises(AuthorizationError):
            authorize("org-a", "u", Action.READ, memberships)

    def test_duplicate_active_membership_fails_closed(self):
        memberships = [
            OrganizationMember("org-a", "u", Role.ADMIN),
            OrganizationMember("org-a", "u", Role.VIEWER),
        ]
        with self.assertRaises(AuthorizationError):
            authorize("org-a", "u", Action.READ, memberships)

    def test_resource_org_mismatch_fails_closed(self):
        with self.assertRaises(AuthorizationError):
            assert_same_organization("org-a", "org-b")


if __name__ == "__main__":
    unittest.main()
