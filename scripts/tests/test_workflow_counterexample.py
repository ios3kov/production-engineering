"""Synthetic example: score-only assertions cannot verify tie ordering.

Example contract: decreasing score, then increasing ASCII name. This is not
an application sorter or evidence that an agent follows the workflow.
"""
import unittest


class RegressionCounterexampleTests(unittest.TestCase):
    def setUp(self):
        # Deliberately put tied names in the opposite of the required order.
        self.input_rows = (("Zoe", 100), ("Miro", 80), ("Ada", 100))
        # Independent expected result from this example's stated contract.
        self.expected = (("Ada", 100), ("Zoe", 100), ("Miro", 80))

    def assert_scores_only(self, result):
        """Intentionally weak: observes scores, but ignores the tied names."""
        self.assertEqual([score for _, score in result], [100, 100, 80])

    def assert_contract(self, result):
        """Verify identities, ordering, scores and count, not only scores."""
        self.assertEqual(result, self.expected)

    def test_weak_check_accepts_both_correct_and_wrong_tie_order(self):
        wrong = tuple(sorted(self.input_rows, key=lambda row: -row[1]))
        self.assertNotEqual(wrong, self.expected)
        self.assert_scores_only(wrong)
        self.assert_scores_only(self.expected)

    def test_contract_check_accepts_correct_fixture(self):
        correct = tuple(sorted(self.input_rows, key=lambda row: (-row[1], row[0])))
        self.assert_contract(correct)

    def test_contract_check_rejects_wrong_tie_order_and_damaged_rows(self):
        wrong_ties = tuple(sorted(self.input_rows, key=lambda row: -row[1]))
        for label, result in (
            ("wrong tie order", wrong_ties),
            ("missing row", self.expected[:-1]),
            ("duplicate row", (self.expected[0], self.expected[0], self.expected[2])),
            ("changed score", (("Ada", 99),) + self.expected[1:]),
        ):
            with self.subTest(case=label), self.assertRaises(AssertionError):
                self.assert_contract(result)


if __name__ == "__main__":
    unittest.main()
