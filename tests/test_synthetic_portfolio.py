import string
import unittest

from govmargin.engine import FindingState
from govmargin.synthetic import EXPECTED, run_synthetic_case


class SyntheticPortfolioTests(unittest.TestCase):
    def test_every_case_a_to_z_has_expected_terminal_truth_state(self):
        self.assertEqual(set(EXPECTED), set(string.ascii_uppercase))
        for letter in string.ascii_uppercase:
            with self.subTest(case=letter):
                self.assertEqual(run_synthetic_case(letter), EXPECTED[letter])

    def test_false_positive_traps_never_emit_recovery(self):
        traps = "CDFGHIKMNORSWXYZ"
        for letter in traps:
            with self.subTest(case=letter):
                self.assertNotEqual(run_synthetic_case(letter), FindingState.RECOVERY_CANDIDATE)

    def test_expected_positive_cases_are_deliberate(self):
        positives = {letter for letter, state in EXPECTED.items() if state == FindingState.RECOVERY_CANDIDATE}
        self.assertEqual(positives, {"B", "E", "J", "L", "P", "Q", "T"})


if __name__ == "__main__":
    unittest.main()
