import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def test_cli_generates_structured_output_and_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            output = temp / "evaluated.json"
            report = temp / "executive.md"

            completed = subprocess.run(
                [
                    sys.executable,
                    "cli.py",
                    "examples/pilot.json",
                    "--output",
                    str(output),
                    "--report",
                    str(report),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output.exists())
            self.assertTrue(report.exists())

            evaluated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                evaluated["summary"]["verified_claim_ready_recovery"],
                "1125000.00",
            )
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("Aviation Recovery — Executive Recovery Report", report_text)
            self.assertIn("Blocked potential:** USD 220,000.00", report_text)


if __name__ == "__main__":
    unittest.main()
