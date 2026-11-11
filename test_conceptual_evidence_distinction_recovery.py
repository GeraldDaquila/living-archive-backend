"""Regression contract for bounded conceptual evidence distinctions."""

import unittest
import general_guide_composition as composition


class ConceptualEvidenceDistinctionTests(unittest.TestCase):
    def test_exact_question_enters_conceptual_recovery_class(self):
        question = "What distinguishes contemplative insight from empirical evidence?"
        self.assertTrue(composition.is_conceptual_relationship_question(question))

    def test_contemplative_insight_and_empirical_evidence_are_answered(self):
        answer = composition._conceptual_relationship_recovery(
            "What distinguishes contemplative insight from empirical evidence?"
        )
        self.assertIsInstance(answer, str)
        self.assertGreaterEqual(len(answer.split()), 90)
        self.assertIn("first-person", answer)
        self.assertIn("observation", answer)
        self.assertIn("different standards of warrant", answer)

    def test_unrelated_concept_pairs_remain_unregistered(self):
        self.assertIsNone(
            composition._conceptual_relationship_recovery(
                "What distinguishes nostalgia from optimism?"
            )
        )


if __name__ == "__main__":
    unittest.main()
