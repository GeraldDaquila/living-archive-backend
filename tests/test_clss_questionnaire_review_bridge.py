"""Tests for the explicit questionnaire-to-review bridge."""
from __future__ import annotations

import unittest

from clss_questionnaire_review_bridge import (
    CLSSQuestionnaireReviewBridgeError,
    normalize_and_review,
)


ANSWERS = [
    {"prompt_id": "responsibility-service", "answer_text": "I am responsible for serving residents.", "source_type": "self_report"},
    {"prompt_id": "concrete-episode", "answer_text": "The meeting was cancelled without notice.", "source_type": "first_hand_observation"},
    {"prompt_id": "consequences", "answer_text": "Residents waited and lost time.", "source_type": "documented_outcome"},
]

REVIEW = {
    "obligation_evidence_ids": ["clss-responsibility-service"],
    "conduct_evidence_ids": ["clss-concrete-episode"],
    "effect_evidence_ids": ["clss-consequences"],
    "counterevidence_ids": [],
    "context_evidence_ids": [],
    "repair_evidence_ids": [],
    "source_conflict_evidence_ids": [],
    "alignment": "supports_tension",
    "context_status": "unknown",
    "repair_status": "unknown",
    "source_status": "consistent",
    "rationale": "The stated responsibility and the described conduct appear to be in tension, with effects reported.",
    "next_action": "Ask what notice was possible and whether a correction was made.",
    "observable_indicators": ["Whether notice was sent", "Whether affected residents were informed"],
}


class QuestionnaireReviewBridgeTests(unittest.TestCase):
    def test_requires_explicit_review_and_does_not_infer_from_answers(self):
        with self.assertRaises(CLSSQuestionnaireReviewBridgeError):
            normalize_and_review(ANSWERS, None, mode="self")

    def test_normalizes_then_composes_cited_review_and_keeps_gaps_visible(self):
        result = normalize_and_review(ANSWERS, REVIEW, mode="self")
        response = result["response"]
        self.assertEqual(response["central_incoherence"]["finding_type"], "mixed_evidence")
        self.assertEqual(response["mode"], "self")
        self.assertEqual(response["path"], "deterministic_fallback")
        self.assertTrue(result["review_required"])
        self.assertIn("coherence", result["missing_dimensions"])
        self.assertIn("counterevidence", result["missing_dimensions"])
        self.assertIn("clss-concrete-episode", response["central_incoherence"]["evidence_ids"])

    def test_no_answered_evidence_fails_closed(self):
        with self.assertRaises(CLSSQuestionnaireReviewBridgeError):
            normalize_and_review(
                [{"prompt_id": "responsibility-service", "answer_text": "   "}],
                REVIEW,
                mode="self",
            )

    def test_third_party_mode_remains_explicit_and_does_not_assert_private_intent(self):
        result = normalize_and_review(ANSWERS, REVIEW, mode="third_party")
        response = result["response"]
        self.assertEqual(response["mode"], "third_party")
        self.assertIn("private intent remains unknown", response["why_it_matters"]["text"])


if __name__ == "__main__":
    unittest.main()
