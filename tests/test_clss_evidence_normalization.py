"""Tests for CLSS questionnaire evidence normalization."""
from __future__ import annotations

import unittest

from clss_evidence_normalization import (
    CLSSNormalizationError,
    normalize_questionnaire_answers,
)


class CLSSEvidenceNormalizationTests(unittest.TestCase):
    def test_preserves_original_text_and_explicit_provenance(self):
        original = "I made the decision after hearing dissent."
        result = normalize_questionnaire_answers(
            [{
                "prompt_id": "concrete-episode",
                "answer_text": original,
                "source_type": "first_hand_observation",
                "context": ["time-critical"],
            }],
            mode="self",
        )
        item = result["evidence"][0]
        self.assertEqual(item["answer_text"], original)
        self.assertEqual(item["dimension"], "conduct")
        self.assertEqual(item["source_type"], "first_hand_observation")
        self.assertTrue(item["provenance"]["source_type_was_explicit"])
        self.assertEqual(item["context"], ["time-critical"])

    def test_missing_source_type_is_unknown_not_guessed(self):
        result = normalize_questionnaire_answers(
            [{"prompt_id": "concrete-episode", "answer_text": "An event occurred."}],
            mode="third_party",
        )
        item = result["evidence"][0]
        self.assertEqual(item["source_type"], "unknown")
        self.assertFalse(item["provenance"]["source_type_was_explicit"])

    def test_missing_answers_are_gaps_not_negative_evidence(self):
        result = normalize_questionnaire_answers(
            [{"prompt_id": "concrete-episode", "answer_text": "I shared the decision."},
             {"prompt_id": "consequences", "answer_text": ""}],
            mode="self",
        )
        self.assertIn("consequences", result["missing_dimensions"])
        self.assertIn("accountability", result["missing_dimensions"])
        self.assertEqual(len(result["evidence"]), 1)
        self.assertTrue(any("gaps, not adverse evidence" in note for note in result["normalization_notes"]))

    def test_unknown_prompt_is_rejected(self):
        with self.assertRaisesRegex(CLSSNormalizationError, "unknown prompt_id"):
            normalize_questionnaire_answers(
                [{"prompt_id": "made-up", "answer_text": "x"}], mode="self"
            )

    def test_duplicate_prompt_is_rejected(self):
        answers = [
            {"prompt_id": "concrete-episode", "answer_text": "first"},
            {"prompt_id": "concrete-episode", "answer_text": "second"},
        ]
        with self.assertRaisesRegex(CLSSNormalizationError, "duplicate prompt_id"):
            normalize_questionnaire_answers(answers, mode="self")

    def test_invalid_source_type_is_rejected(self):
        with self.assertRaisesRegex(CLSSNormalizationError, "invalid source_type"):
            normalize_questionnaire_answers(
                [{"prompt_id": "concrete-episode", "answer_text": "x", "source_type": "rumor"}],
                mode="third_party",
            )

    def test_invalid_mode_is_rejected(self):
        with self.assertRaisesRegex(CLSSNormalizationError, "mode must be"):
            normalize_questionnaire_answers([], mode="committee")


if __name__ == "__main__":
    unittest.main()
