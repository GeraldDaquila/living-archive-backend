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
        self.assertIn("general", snapshot["question_shapes"])


if __name__ == "__main__":
    unittest.main()
