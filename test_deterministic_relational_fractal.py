"""Simulated-question regression tests for the deterministic relational fractal."""
import unittest

from deterministic_relational_fractal import CONTRACT_VERSION, STAGES, compose_relational_fractal


SIMULATED_QUESTIONS = [
    ("My friend has become distant and I always initiate contact. They reply, but rarely reach out. What does this mean?", True, "contact"),
    ("My partner says I criticize them whenever I bring up chores, then they go quiet. I list everything I have done.", True, "conflict"),
    ("My colleague and I disagree about workload, and I feel blamed whenever I ask to rebalance it.", True, "workload"),
    ("I keep reaching out to my sibling, but they rarely respond and I do not know where we stand.", True, "distance"),
    ("My wife says I do not listen, while I feel I am trying to explain myself.", True, "being heard"),
    ("My friend likes hiking and sent me a picture of a trail.", False, None),
    ("What is stewardship?", False, None),
    ("My partner is wonderful and I love our relationship.", False, None),
    ("My coworker missed the deadline and I am unsure what happened.", False, None),
    ("My parent goes silent after disagreements and I am left wondering how to reconnect.", True, "conflict"),
    ("My sibling keeps cancelling plans, and I am usually the one trying to arrange another time.", True, "contact"),
    ("My partner and I have the same argument about chores. I want to understand what happens between us.", True, "conflict"),
]


class DeterministicRelationalFractalTests(unittest.TestCase):
    def test_supported_questions_return_four_ordered_movements(self):
        for question, supported, _signal in SIMULATED_QUESTIONS:
            with self.subTest(question=question):
                result = compose_relational_fractal(question)
                if not supported:
                    self.assertIsNone(result)
                    continue
                self.assertIsNotNone(result)
                self.assertEqual(result["fractal_contract"], CONTRACT_VERSION)
                self.assertEqual(result["fractal_stages"], STAGES)
                paragraphs = result["response"].split("\n\n")
                self.assertEqual(len(paragraphs), 4)
                self.assertTrue(paragraphs[0].endswith("."))
                self.assertIn("may", paragraphs[1].casefold())
                self.assertTrue(paragraphs[3].endswith("?"))
                self.assertEqual(paragraphs[3].count("?"), 1)

    def test_observation_uses_query_evidence(self):
        q = "My partner says I criticize them whenever I bring up chores, then they go quiet."
        result = compose_relational_fractal(q)
        self.assertIsNotNone(result)
        self.assertIn("chores", result["response"].casefold())
        self.assertIn("go quiet", result["response"].casefold())
        self.assertTrue(result["fractal_evidence"]["observation_grounded_in_query"])

    def test_does_not_claim_to_know_another_persons_motive(self):
        for q, supported, _signal in SIMULATED_QUESTIONS:
            if not supported:
                continue
            with self.subTest(question=q):
                result = compose_relational_fractal(q)
                self.assertIsNotNone(result)
                self.assertFalse(result["fractal_evidence"]["motive_inference"])
                self.assertNotIn("they don't care", result["response"].casefold())
                self.assertNotIn("they hate me", result["response"].casefold())

    def test_inquiry_is_one_question_and_contextual_to_pattern(self):
        q = "My partner says I criticize them whenever I bring up chores, then they go quiet."
        result = compose_relational_fractal(q)
        self.assertIsNotNone(result)
        inquiry = result["response"].split("\n\n")[-1]
        self.assertEqual(inquiry.count("?"), 1)
        self.assertIn("pattern", inquiry.casefold())

    def test_unrelated_or_underspecified_questions_remain_out_of_scope(self):
        for q in ("", "My friend likes hiking.", "What is stewardship?",
                  "My partner is wonderful and I love our relationship."):
            with self.subTest(question=q):
                self.assertIsNone(compose_relational_fractal(q))


if ( __name__ == "__main__"):
    unittest.main()
