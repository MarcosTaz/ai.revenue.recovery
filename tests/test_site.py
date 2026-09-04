from pathlib import Path
import unittest


class AervindLandingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = Path("index.html").read_text(encoding="utf-8")
        cls.lower = cls.html.lower()

    def test_brand_and_offer_are_present(self):
        self.assertIn("AERVIND", self.html)
        self.assertIn("Aviation Lease Entitlement Recovery", self.html)
        self.assertIn("Recovery Scan", self.html)
        self.assertIn("€9,500", self.html)
        self.assertIn("Up to 5", self.html)
        self.assertIn("10 business days", self.html)

    def test_first_scan_does_not_require_live_system_access(self):
        self.assertIn("No live system access required", self.html)
        self.assertIn("PDFs, spreadsheets and controlled exports", self.html)
        self.assertIn("Do you need access to our systems?", self.html)

    def test_recovery_truth_boundary_is_public(self):
        self.assertIn("A claim is not recovery", self.html)
        self.assertIn("settlement evidence", self.lower)

    def test_no_guaranteed_recovery_claim(self):
        self.assertNotIn("guaranteed recovery", self.lower)
        self.assertNotIn("guarantee recovery", self.lower)
        self.assertIn("does not guarantee", self.lower)

    def test_no_false_regulated_positioning(self):
        self.assertIn("not legal counsel", self.lower)
        self.assertIn("statutory auditor", self.lower)
        self.assertIn("airworthiness authority", self.lower)

    def test_launch_legal_supplier_disclosure_exists(self):
        self.assertIn("real legal supplier", self.lower)


if __name__ == "__main__":
    unittest.main()
