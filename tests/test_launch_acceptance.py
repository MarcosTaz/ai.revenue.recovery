from pathlib import Path
import unittest


class AervindLaunchAcceptanceTests(unittest.TestCase):
    CANONICAL_BUYER_FILES = (
        Path("README.md"),
        Path("index.html"),
        Path("docs/CAPABILITY_STATEMENT.md"),
        Path("docs/FIRST_PAID_RECOVERY_SCAN_PROPOSAL.md"),
        Path("docs/PILOT_SOW.md"),
        Path("docs/PILOT_DATA_REQUEST.md"),
        Path("docs/CLIENT_INTAKE_README.md"),
        Path("docs/GTM.md"),
        Path("docs/OUTBOUND_PLAYBOOK.md"),
    )

    @classmethod
    def setUpClass(cls):
        cls.buyer_text = {
            path: path.read_text(encoding="utf-8") for path in cls.CANONICAL_BUYER_FILES
        }
        cls.launch = Path("docs/LAUNCH_CHECKLIST.md").read_text(encoding="utf-8")
        cls.email_ops = Path("docs/EMAIL_OPERATIONS.md").read_text(encoding="utf-8")
        cls.readme = Path("README.md").read_text(encoding="utf-8")

    def test_canonical_first_scan_price_is_consistent(self):
        for path, text in self.buyer_text.items():
            with self.subTest(path=path):
                self.assertTrue(
                    "€9,500" in text or "EUR 9,500" in text,
                    f"{path} must state the canonical EUR 9,500 first scan",
                )

    def test_canonical_first_scan_scope_is_consistent(self):
        required_meanings = (
            ("5", "aircraft"),
            ("1", "entitlement"),
            ("12", "months"),
            ("10", "business days"),
        )
        for path, text in self.buyer_text.items():
            lowered = text.lower()
            with self.subTest(path=path):
                for number, term in required_meanings:
                    self.assertIn(number, lowered)
                    self.assertIn(term, lowered)

    def test_legacy_first_scan_ranges_do_not_reappear(self):
        forbidden = (
            "3–10 aircraft",
            "3-10 aircraft",
            "1–3 entitlement",
            "1-3 entitlement",
            "12–24 months",
            "12-24 months",
            "€7,500–15,000",
            "EUR 7,500–15,000",
            "EUR 7.5k–15k",
        )
        for path, text in self.buyer_text.items():
            with self.subTest(path=path):
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)

    def test_first_scan_does_not_require_live_customer_system_access(self):
        key_files = (
            Path("README.md"),
            Path("index.html"),
            Path("docs/CAPABILITY_STATEMENT.md"),
            Path("docs/FIRST_PAID_RECOVERY_SCAN_PROPOSAL.md"),
            Path("docs/PILOT_DATA_REQUEST.md"),
            Path("docs/GTM.md"),
            Path("docs/OUTBOUND_PLAYBOOK.md"),
        )
        for path in key_files:
            lowered = self.buyer_text[path].lower()
            with self.subTest(path=path):
                self.assertIn("no", lowered)
                self.assertTrue(
                    "live" in lowered and "system" in lowered,
                    f"{path} must explain that the first scan needs no live system access",
                )

    def test_domain_ownership_truth_is_recorded(self):
        self.assertIn("aervind.com", self.launch)
        self.assertIn("registered through Porkbun", self.launch)
        self.assertIn("[x] Purchase **aervind.com**", self.launch)
        self.assertIn("registered through Porkbun", self.readme)

    def test_real_outreach_hold_is_fail_closed(self):
        launch = self.launch.upper()
        mail = self.email_ops.upper()
        readme = self.readme.upper()
        self.assertIn("NO REAL OUTREACH", launch)
        self.assertIn("NO REAL EXTERNAL SEND", mail)
        self.assertIn("DO NOT SEND", mail)
        self.assertIn("EXPLICITLY LIFTS THIS HOLD", launch)
        self.assertIn("REAL OUTREACH: HOLD ACTIVE", readme)
        self.assertNotIn("COMMERCIAL OUTREACH OPEN", readme)

    def test_dns_verification_is_separate_from_real_recipient_test(self):
        self.assertIn("DNS-verified", self.email_ops)
        self.assertIn("externally delivery-tested", self.email_ops)
        self.assertIn("real external recipient", self.email_ops)


if __name__ == "__main__":
    unittest.main()
