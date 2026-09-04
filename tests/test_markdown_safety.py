import unittest

from claim_package import render_external_claim_markdown
from executive_report import render_executive_markdown
from markdown_safety import markdown_plain_text


class MarkdownArtifactSafetyTests(unittest.TestCase):
    def test_plain_text_collapses_structure_and_preserves_normal_references(self):
        self.assertEqual(markdown_plain_text("Lease.pdf#MR"), "Lease.pdf#MR")
        rendered = markdown_plain_text("A|B\n## forged <script>x</script> [click](javascript:x) **bold**")
        self.assertNotIn("\n", rendered)
        self.assertIn("A\\|B", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("\\[click\\]", rendered)
        self.assertIn("\\*\\*bold\\*\\*", rendered)

    def test_claim_package_cannot_be_restructured_by_untrusted_metadata(self):
        dossier = {
            "externalization_gate": "passed",
            "blocking_issues": [],
            "lineage_gaps": [],
            "claim": {
                "claim_id": "C-1\n## FORGED SECTION",
                "entitlement_type": "maintenance|reserve",
                "event_date": "2026-06-01",
                "currency": "USD",
                "gross_entitlement": "100",
                "net_recoverable": "80",
                "rule_id": "R-1",
            },
            "rule": {
                "formula": "lower_of_cost_and_fund",
                "effective_from": "2026-01-01",
                "effective_to": None,
                "contribution_rate": "1",
                "cap": None,
                "floor": None,
                "deductible": "0",
            },
            "financial_inputs": {
                "eligible_cost": "100",
                "available_fund": "80",
                "prior_paid_or_reimbursed": "0",
                "claimed_to_date": "0",
            },
            "evidence": [
                {
                    "evidence_id": "E-1",
                    "evidence_type": "invoice",
                    "source_name": "Invoice.pdf\n<script>alert(1)</script> | injected",
                }
            ],
            "source_refs": {
                "rule_source": "Lease.pdf#MR\n## fake heading",
            },
            "calculation_trace": ["step one\n## fake trace"],
        }

        rendered = render_external_claim_markdown(dossier)
        self.assertNotIn("\n## FORGED SECTION", rendered)
        self.assertNotIn("\n## fake heading", rendered)
        self.assertNotIn("\n## fake trace", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("maintenance\\|reserve", rendered)
        self.assertIn("Lease.pdf#MR", rendered)

    def test_executive_table_cannot_gain_columns_or_sections_from_claim_data(self):
        evaluated = {
            "summary": {
                "currency": "USD",
                "review_required_pipeline": "0",
                "blocked_potential": "0",
                "candidate_count": 1,
            },
            "results": [
                {
                    "claim_id": "C-1|EXTRA\n## FORGED",
                    "status": "claim_ready",
                    "net_recoverable": "80",
                    "currency": "USD",
                    "blocking_issues": [],
                    "warnings": ["warning|extra\n<script>x</script>"],
                }
            ],
        }
        rendered = render_executive_markdown(evaluated)
        self.assertNotIn("\n## FORGED", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn("C-1\\|EXTRA", rendered)
        self.assertIn("warning\\|extra", rendered)
        self.assertIn("&lt;script&gt;", rendered)


if __name__ == "__main__":
    unittest.main()
