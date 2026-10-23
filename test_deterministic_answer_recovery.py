import unittest

from deterministic_answer_recovery import compose_recovery, contract_snapshot


class DeterministicAnswerRecoveryTests(unittest.TestCase):
    def test_each_question_shape_returns_substantive_text(self):
        cases = {
            "Why do public institutions lose trust?": "evidence",
            "How can a community allocate a limited budget?": "outcome",
            "What is institutional responsibility?": "clear account",
            "Compare personal agency and responsibility.": "comparison",
            "Should we change the policy now?": "decision",
            "Help me understand a difficult situation.": "known",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                answer = compose_recovery(question)
                self.assertGreater(len(answer), 120)
                self.assertIn(expected, answer.casefold())

    def test_hindsight_accountability_precedes_generic_decision_recovery(self):
        question = (
            "If the group made the best decision it could with the information available at the time, "
            "how should it distinguish genuine accountability from unfairly blaming people in hindsight?"
        )
        answer = compose_recovery(question)
        self.assertIn("information, constraints, and alternatives available at the time", answer)
        self.assertIn("Hindsight blame assumes", answer)
        self.assertIn("warnings or dissent", answer)
        self.assertIn("A harmful result, by itself, does not prove", answer)
        self.assertIn("improving the decision process", answer)
        self.assertNotIn("choose one step small enough to test", answer)
        self.assertNotIn("What detail or context", answer)

    def test_hindsight_accountability_classifier_does_not_capture_ordinary_decisions(self):
        answer = compose_recovery("Should we change the policy now?")
        self.assertIn("The decision about", answer)
        self.assertIn("limited trial", answer)
        self.assertNotIn("Hindsight blame assumes", answer)

    def test_ethical_tradeoff_precedes_generic_how_to_recovery(self):
        question = (
            "What if each person sincerely believes they are protecting something important, "
            "but protecting one person's priorities means another person will lose something "
            "they deeply value? How should we decide what to protect?"
        )
        answer = compose_recovery(question)
        self.assertIn("who has the power to decide", answer)
        self.assertIn("can be repaired from those that cannot", answer)
        self.assertIn("least power", answer)
        self.assertIn("justify that choice", answer)
        self.assertNotIn("choose one step small enough to test", answer)
        self.assertNotIn("What detail or context", answer)

    def test_gold_standard_stewardship_question_keeps_its_own_response_shape(self):
        question = "What does stewardship look like when people disagree about what is worth protecting?"
        answer = compose_recovery(question)
        self.assertIn("different values, responsibilities, or fears", answer)
        self.assertIn("who would bear the costs", answer)
        self.assertIn("disagreement responsibly, not to erase it", answer)
        self.assertNotIn("What detail or context", answer)

    def test_ethical_tradeoff_does_not_trigger_for_ordinary_practical_question(self):
        answer = compose_recovery("How can a team coordinate a project rollout?")
        self.assertIn("clarify what a good outcome would look like", answer)
        self.assertIn("Choose one small step", answer)
        self.assertNotIn("least power", answer)

    def test_never_claims_archive_source_or_provider_success(self):
        answer = compose_recovery("What is institutional responsibility?")
        self.assertNotIn("the Archive says", answer.casefold())
        self.assertNotIn("I found a source", answer.casefold())
        self.assertNotIn("provider bank", answer.casefold())

    def test_empty_question_is_humane_and_bounded(self):
        self.assertEqual(compose_recovery(""), "What would you like to understand or work through?")

    def test_contract_snapshot_is_provider_independent(self):
        snapshot = contract_snapshot()
        self.assertTrue(snapshot["provider_independent"])
        self.assertTrue(snapshot["does_not_invent_archive_evidence"])
        self.assertIn("hindsight_accountability", snapshot["question_shapes"])
        self.assertIn("ethical_tradeoff", snapshot["question_shapes"])
        self.assertIn("general", snapshot["question_shapes"])


if __name__ == "__main__":
    unittest.main()
