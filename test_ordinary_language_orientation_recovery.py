"""Regression contract for ordinary-language orientation recovery."""

import unittest
import general_guide_composition as composition
import main


class OrdinaryLanguageOrientationRecoveryTests(unittest.TestCase):
    QUESTION = "What does it mean to recover orientation during a season of uncertainty?"

    def test_exact_question_is_orientation_sensitive(self):
        self.assertTrue(composition._requires_orientation_anchor(self.QUESTION))

    def test_exact_question_receives_bounded_orientation(self):
        answer = composition._ordinary_language_orientation_recovery(self.QUESTION)
        self.assertIsInstance(answer, str)
        self.assertGreaterEqual(len(answer.split()), 100)
        self.assertNotIn("can't define", answer.casefold())
        self.assertNotIn("cannot define", answer.casefold())
        self.assertIn("where you are", answer)
        self.assertIn("what matters", answer)
        self.assertIn("does not require solving the uncertainty", answer.casefold())
        self.assertIn("place to stand", answer.casefold())
        self.assertIn("next responsible step", answer.casefold())

    def test_unrelated_definition_question_is_not_captured(self):
        self.assertIsNone(
            composition._ordinary_language_orientation_recovery(
                "What does it mean to define institutional accountability?"
            )
        )

    def test_runtime_boundary_preserves_ordinary_orientation_after_evidence_miss(self):
        answer = main._ordinary_orientation_boundary_recovery(self.QUESTION)
        self.assertIsInstance(answer, str)
        self.assertIn("where you are", answer)
        self.assertIn("what matters", answer)
        self.assertNotIn("can't define", answer.casefold())
        self.assertNotIn("cannot define", answer.casefold())

    def test_runtime_boundary_does_not_capture_unrelated_definition(self):
        self.assertIsNone(
            main._ordinary_orientation_boundary_recovery(
                "What does it mean to define institutional accountability?"
            )
        )


if __name__ == "__main__":
    unittest.main()
