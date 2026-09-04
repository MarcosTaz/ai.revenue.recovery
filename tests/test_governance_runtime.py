from pathlib import Path
import json
import unittest


class AervindGovernanceRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.procurement = Path("docs/PROCUREMENT_READINESS.md").read_text(encoding="utf-8")
        cls.readiness = Path("docs/READINESS.md").read_text(encoding="utf-8")
        cls.security = Path("docs/SECURITY_AND_CONFIDENTIALITY.md").read_text(encoding="utf-8")
        cls.launch = Path("docs/LAUNCH_CHECKLIST.md").read_text(encoding="utf-8")
        cls.vercel = json.loads(Path("vercel.json").read_text(encoding="utf-8"))

    def test_procurement_never_treats_product_readiness_as_send_authority(self):
        upper = self.procurement.upper()
        self.assertIn("REAL OUTREACH: HOLD ACTIVE", upper)
        self.assertIn("HOLD NOW", upper)
        self.assertNotIn("GO FOR COMMERCIAL OUTREACH NOW", upper)
        self.assertIn("EUR 9,500", self.procurement)
        self.assertIn("5 aircraft", self.procurement)
        self.assertIn("1 primary entitlement family", self.procurement)
        self.assertIn("12 months", self.procurement)
        self.assertIn("10 business days", self.procurement)

    def test_readiness_separates_product_from_external_execution(self):
        upper = self.readiness.upper()
        self.assertIn("PRODUCT / DELIVERY: ASSISTED PILOT READY", upper)
        self.assertIn("REAL OUTREACH: HOLD ACTIVE", upper)
        self.assertIn("TEMPORARY VERCEL HOST LIVE", upper)
        self.assertIn("CUSTOM ROUTING PENDING", upper)
        self.assertIn("BRANDED EMAIL: DNS CONFIGURATION PENDING", upper)

    def test_security_document_matches_loopback_only_implementation(self):
        lowered = self.security.lower()
        self.assertIn("refuses non-loopback bind addresses", lowered)
        self.assertIn("host", lowered)
        self.assertIn("origin", lowered)
        self.assertIn("2 mb", lowered)
        self.assertIn("claims we do not make", lowered)
        self.assertIn("soc 2", lowered)
        self.assertIn("iso 27001", lowered)

    def test_launch_truth_does_not_claim_official_domain_or_mail_live(self):
        lowered = self.launch.lower()
        self.assertIn("technical temporary host", lowered)
        self.assertIn("must therefore **not** be described as live or verified", lowered)
        self.assertIn("attach **aervind.com**", lowered)

    def test_temporary_host_is_noindex_until_custom_domain_launch(self):
        headers = []
        for rule in self.vercel.get("headers", []):
            headers.extend(rule.get("headers", []))
        by_key = {item.get("key"): item.get("value") for item in headers}
        self.assertEqual(by_key.get("X-Robots-Tag"), "noindex, nofollow")


if __name__ == "__main__":
    unittest.main()
