import unittest

import main


class ConceptualPracticalStewardshipBoundaryTests(unittest.TestCase):
    def test_trust_role_question_is_not_misclassified_as_practical(self):
        query = "What is the role of trust in community stewardship?"
        self.assertTrue(main._is_conceptual_explanatory_request(query))
        self.assertFalse(main._is_practical_stewardship_question(query))

    def test_practical_stewardship_question_keeps_practical_path(self):
        query = "How do I practice stewardship in everyday community decisions?"
        self.assertFalse(main._is_conceptual_explanatory_request(query))
        self.assertTrue(main._is_practical_stewardship_question(query))


if __name__ == "__main__":
    unittest.main()
