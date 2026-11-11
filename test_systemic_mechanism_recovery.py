"""Regression contract for systemic mechanism recovery."""

import unittest
import general_guide_composition as composition


class SystemicMechanismRecoveryTests(unittest.TestCase):
    QUESTION = "How can algorithmic systems scale existing biases or institutional failures?"

    def test_exact_question_enters_conceptual_recovery_class(self):
        self.assertTrue(composition.is_conceptual_relationship_question(self.QUESTION))

    def test_exact_question_receives_mechanism_explanation(self):
        answer = composition._conceptual_relationship_recovery(self.QUESTION)
        self.assertIsInstance(answer, str)
        self.assertGreaterEqual(len(answer.split()), 180)
        self.assertIn("learn from, formalize, or operate within patterns that already exist", answer)
        self.assertIn("Scale also changes the consequences of error", answer)
        self.assertIn("Feedback can deepen the problem", answer)
        self.assertIn("who remains responsible", answer)
        self.assertNotIn("couldn't verify a reliable answer", answer.casefold())

    def test_second_amplification_question_uses_same_class(self):
        self.assertTrue(
            composition.is_conceptual_relationship_question(
                "How can automated systems reinforce existing institutional failures?"
            )
        )

    def test_non_mechanism_question_is_not_captured(self):
        self.assertIsNone(
            composition._conceptual_relationship_recovery(
                "How can a person improve their handwriting?"
            )
        )


if __name__ == "__main__":
    unittest.main()
