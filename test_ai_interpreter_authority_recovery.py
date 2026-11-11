"""Regression contract for AI interpreter-versus-authority conceptual recovery."""
import unittest
import general_guide_composition as g

QUESTION = "What does it mean for an AI to be an interpreter rather than an authority?"

class AIInterpreterAuthorityRecoveryTests(unittest.TestCase):
    def test_exact_question_recovers_without_provider(self):
        answer = g._conceptual_relationship_recovery(QUESTION)
        self.assertTrue(answer)
        self.assertIn("help people make sense of information", answer)
        self.assertIn("final right to decide", answer)

    def test_answer_preserves_responsibility_boundary(self):
        answer = g._conceptual_relationship_recovery(QUESTION)
        self.assertIn("human and institutional responsibility", answer)
        self.assertIn("values they uphold", answer)

    def test_answer_is_orientation_not_false_archive_definition(self):
        answer = g._conceptual_relationship_recovery(QUESTION)
        self.assertIn("general conceptual distinction", answer)
        self.assertIn("not a claim that every institution defines", answer)

    def test_unrelated_ai_question_is_not_captured(self):
        self.assertIsNone(
            g._conceptual_relationship_recovery(
                "What is the fastest way to train an AI model?"
            )
        )

if __name__ == "__main__":
    unittest.main()
