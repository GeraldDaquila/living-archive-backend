import unittest

from deterministic_answer_recovery import compose_recovery, contract_snapshot


class DeterministicAnswerRecoveryTests(unittest.TestCase):
    def test_each_question_shape_returns_substantive_text(self):
        cases = {
            "Why do public institutions lose trust?": "evidence",
            "How can a community allocate a limited budget?": "outcome",
            "What is institutional responsibility?": "is best understood",
            "Compare personal agency and responsibility.": "comparison",
            "Should we change the policy now?": "decision",
            "Help me understand a difficult situation.": "known",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                answer = compose_recovery(question)
                self.assertGreater(len(answer), 120)
                self.assertIn(expected, answer.casefold())


    def test_competing_stakeholder_obligations_gets_substantive_gold_standard_recovery(self):
        question = "How can leaders hold competing stakeholder obligations?"
        answer = compose_recovery(question)
        paragraphs = [part.strip() for part in answer.split("\\n\\n") if part.strip()]
        self.assertEqual(len(paragraphs), 3)
        self.assertIn("competing stakeholder obligations", paragraphs[0].casefold())
        self.assertIn("who carries the cost", paragraphs[1].casefold())
        self.assertIn("those with less power", paragraphs[2].casefold())
        self.assertNotIn("choose one step small enough to test", answer)
        self.assertNotIn("I couldn’t produce a reliable answer", answer)

    def test_substantive_recovery_defaults_to_three_paragraphs_across_question_shapes(self):
        questions = (
            "Why do public institutions lose trust?",
            "How can a community allocate a limited budget?",
            "What is institutional responsibility?",
            "Should we change the policy now?",
            "Help me understand a difficult situation.",
        )
        for question in questions:
            with self.subTest(question=question):
                answer = compose_recovery(question)
                self.assertEqual(len([p for p in answer.split("\\n\\n") if p.strip()]), 3)

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
        self.assertIn("define the outcome you want", answer)
        self.assertIn("choose one step small enough to test", answer)
        self.assertNotIn("least power", answer)

    def test_answerable_definition_is_direct_and_not_a_meta_template(self):
        answer = compose_recovery("What is institutional responsibility?")
        self.assertIn("is best understood", answer)
        self.assertIn("general explanation", answer)
        self.assertNotIn("Your question asks for a clear account", answer)
        self.assertNotIn("A useful explanation should establish", answer)
        self.assertNotIn("What detail or context would make this question", answer)

    def test_institutional_orientation_answers_what_it_is_and_is_not(self):
        answer = compose_recovery("What is the Living Archive, and what is it not?")
        paragraphs = [part for part in answer.split("\n\n") if part.strip()]
        self.assertEqual(len(paragraphs), 3)
        self.assertIn("public knowledge commons", answer)
        self.assertIn("orientation ecosystem", answer)
        self.assertIn("human flourishing", answer)
        self.assertIn("constitutional sensemaking", answer)
        self.assertIn("claims should be distinguishable from interpretation and inference", answer)
        self.assertIn("uncertainty should be acknowledged", answer)
        self.assertIn("human judgment", answer)
        self.assertIn("not a chatbot", answer)
        self.assertIn("not to decide for the visitor", answer)
        self.assertNotIn("A useful response should", answer)
        self.assertNotIn("general institutional orientation", answer)
        self.assertNotIn("material retrieved for any one question", answer)
        self.assertNotIn("Your question asks for a clear account", answer)
        self.assertNotIn("A useful explanation should establish", answer)
        self.assertNotIn("What detail or context would make this question", answer)

    def test_genuinely_missing_subject_is_handled_by_request_boundary_not_generic_recovery(self):
        answer = compose_recovery("What is this problem?")
        self.assertNotIn("What detail or context would make this question", answer)
        self.assertGreater(len(answer), 80)

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
