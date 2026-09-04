from pathlib import Path
import unittest


class AervindRealOutreachHoldTests(unittest.TestCase):
    def test_hold_document_is_active_and_explicit(self):
        text = Path("docs/REAL_OUTREACH_HOLD.md").read_text(encoding="utf-8")
        upper = text.upper()
        self.assertIn("STATUS: **ACTIVE**", upper)
        self.assertIn("DO NOT SEND ANYTHING TO ANY REAL PERSON OR ORGANIZATION", upper)
        self.assertIn("ONLY A NEW EXPLICIT FOUNDER INSTRUCTION", upper)

    def test_mail_operations_fail_closed_during_hold(self):
        text = Path("docs/EMAIL_OPERATIONS.md").read_text(encoding="utf-8").upper()
        self.assertIn("NO REAL EXTERNAL SEND", text)
        self.assertIn("DO NOT SEND", text)
        self.assertIn("REAL EXTERNAL RECIPIENT", text)

    def test_launch_checklist_recognizes_hold_priority(self):
        text = Path("docs/LAUNCH_CHECKLIST.md").read_text(encoding="utf-8").upper()
        self.assertIn("NO REAL OUTREACH / NO REAL EXTERNAL SEND", text)
        self.assertIn("THE HOLD OVERRIDES ANY OLDER DOCUMENT", text)


if __name__ == "__main__":
    unittest.main()
