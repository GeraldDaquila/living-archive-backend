"""Regression contract for stewardship-centered technology role recovery."""

import unittest
import general_guide_composition as composition


class StewardshipTechnologyRoleRecoveryTests(unittest.TestCase):
    QUESTION = "What role should technology play in a stewardship-centered society?"

    def test_exact_question_enters_conceptual_recovery_class(self):
        self.assertTrue(composition.is_conceptual_relationship_question(self.QUESTION))

    def test_exact_question_receives_substantive_role_orientation(self):
        answer = composition._conceptual_relationship_recovery(self.QUESTION)
        self.assertIsInstance(answer, str)
        self.assertGreaterEqual(len(answer.split()), 120)
        self.assertIn("means rather than the thing that sets the direction", answer)
        self.assertIn("human judgment and accountable governance", answer)
        self.assertIn("long-term responsibility", answer)
        self.assertIn("who benefits", answer.casefold())
        self.assertIn("who retains agency", answer.casefold())
        self.assertIn("caring for", answer.casefold())
        self.assertNotIn("couldn't produce a reliable answer", answer.casefold())

    def test_second_institutional_role_question_uses_same_structural_path(self):
        answer = composition._conceptual_relationship_recovery(
            "What role should transparency play in public governance?"
        )
        self.assertIsInstance(answer, str)
        self.assertIn("means rather than the thing that sets the direction", answer)
        self.assertIn("human judgment and accountable governance", answer)

    def test_non_institutional_role_question_is_not_captured(self):
        self.assertIsNone(
            composition._conceptual_relationship_recovery(
                "What role should nostalgia play in a successful holiday?"
            )
        )


if __name__ == "__main__":
    unittest.main()
