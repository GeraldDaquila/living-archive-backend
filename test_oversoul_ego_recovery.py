"""Regression contract for substantive Oversoul/ego answers and generic-meta rejection."""
import unittest

import general_guide_composition
from deterministic_answer_recovery import (
    compose_recovery,
    has_registered_recovery,
    registered_recovery_recommendation,
)


QUESTION = (
    "Does the Oversoul have final say in a person's life outcome, or is there "
    "an inherent conflict between the ego and Oversoul prior to awakening?"
)

GENERIC_META_ANSWER = (
    "The question about the Oversoul can be approached by first identifying the main issue and the decision or understanding at stake. "
    "A useful answer should distinguish what is established from what is inferred rather than fill gaps with confidence.\n\n"
    "The next step is to examine the most relevant facts, relationships, and plausible explanations. "
    "Ask which evidence would distinguish them, whose perspective may be missing, and whether any assumption is doing more work than the facts justify.\n\n"
    "This provides a grounded starting point without pretending to know details the question has not supplied. "
    "Where the evidence is incomplete, say what can reasonably be concluded and what remains open, instead of replacing the answer with a generic refusal."
)


class OversoulEgoRecoveryTests(unittest.TestCase):
    def test_substantive_question_is_registered(self):
        self.assertTrue(has_registered_recovery(QUESTION))

    def test_provider_quality_gate_rejects_screenshot_style_meta_answer(self):
        self.assertTrue(
            general_guide_composition.is_generic_nonanswer(
                QUESTION, GENERIC_META_ANSWER
            )
        )

    def test_deterministic_recovery_answers_both_sides_of_question(self):
        answer = compose_recovery(QUESTION)
        paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]
        self.assertEqual(len(paragraphs), 3)
        self.assertIn("final say", answer.lower())
        self.assertIn("ego and oversoul are enemies", answer.lower())
        self.assertIn("personal agency", answer.lower())
        self.assertIn("not an empirically verifiable account", answer.lower())
        self.assertNotIn("the next step is to examine", answer.lower())
        self.assertNotIn("grounded starting point", answer.lower())

    def test_recovery_has_direct_canonical_oversoul_doorway(self):
        doorway = registered_recovery_recommendation(QUESTION)
        self.assertEqual(
            doorway["title"],
            "Eternal / Oversoul Law – The Immutable Jurisdiction",
        )
        self.assertEqual(
            doorway["url"],
            "https://geralddaquila.com/oversoul-law",
        )
        self.assertIn("not independent evidence", doorway["rationale"])

    def test_family_does_not_capture_unrelated_questions(self):
        self.assertFalse(
            has_registered_recovery("How does the ego shape identity before awakening?")
        )
        self.assertFalse(
            has_registered_recovery("Does the Oversoul exist?")
        )
        self.assertFalse(has_registered_recovery("What is the capital of Japan?"))


if __name__ == "__main__":
    unittest.main()
