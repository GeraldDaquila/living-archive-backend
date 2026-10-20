"""Regression tests for the deterministic relational fractal."""
import unittest

from deterministic_relational_fractal import CONTRACT_VERSION, compose_relational_fractal


class DeterministicRelationalFractalTests(unittest.TestCase):
    def test_four_movements_are_present_in_order(self):
        result = compose_relational_fractal(
            "My friend has become distant and I always initiate contact. "
            "They reply, but rarely reach out. What does this mean?"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["fractal_contract"], CONTRACT_VERSION)
        self.assertEqual(
            result["fractal_stages"],
            ["observation", "implication", "so_what", "inquiry"],
        )
        paragraphs = result["response"].split("\n\n")
        self.assertEqual(len(paragraphs), 4)
        self.assertIn("observe", paragraphs[0].casefold())
        self.assertIn("does not by itself tell us why", paragraphs[1])
        self.assertIn("mutual", paragraphs[2])
        self.assertEqual(paragraphs[3].count("?"), 1)

    def test_does_not_claim_to_know_the_other_persons_motive(self):
        result = compose_relational_fractal(
            "My partner is distant and I keep reaching out. Why?"
        )
        self.assertIsNotNone(result)
        self.assertIn("still open questions", result["response"])
        self.assertNotIn("they don't care", result["response"].casefold())

    def test_unrelated_or_non_relational_question_is_unchanged(self):
        self.assertIsNone(compose_relational_fractal("What is stewardship?"))
        self.assertIsNone(compose_relational_fractal("My friend likes hiking."))


if __name__ == "__main__":
    unittest.main()
