"""Regression coverage for foundation-answer recovery when providers are exhausted."""

import unittest
from unittest.mock import patch

import main


class FoundationProviderExhaustionRecoveryTests(unittest.TestCase):
    @patch("main._compose_provider_exhaustion_recovery")
    @patch("main._basic_inquiry_round1_deterministic_response")
    def test_living_archive_definition_survives_provider_exhaustion(
        self, deterministic_response, provider_recovery
    ):
        deterministic_response.return_value = {
            "response": "I couldn't verify a reliable answer from the material available.",
            "doorway_title": "",
            "provider": "deterministic_question_preserving_recovery",
            "model": "",
        }

        result = main._basic_inquiry_provider_exhaustion_response(
            "What is the Living Archive?",
            {},
            {},
            recommendation_available=False,
        )

        self.assertEqual(
            result["provider"],
            "bounded_foundation_provider_exhaustion_recovery",
        )
        self.assertIn("connected body of essays", result["response"])
        self.assertIn("finding your bearings", result["response"])
        self.assertIn("Recover, Remember, Apply, and Refine", result["response"])
        self.assertEqual(len(result["response"].split("\n\n")), 3)
        self.assertEqual(result["doorway_title"], "")
        self.assertIsNone(result["recommendation"])
        provider_recovery.assert_not_called()

    @patch("main._compose_provider_exhaustion_recovery")
    @patch("main._basic_inquiry_round1_deterministic_response")
    def test_foundation_recovery_does_not_capture_unrelated_questions(
        self, deterministic_response, provider_recovery
    ):
        deterministic_response.return_value = {
            "response": "I couldn't verify a reliable answer from the material available.",
            "doorway_title": "",
            "provider": "deterministic_question_preserving_recovery",
            "model": "",
        }
        provider_recovery.return_value = (
            "I couldn't verify a reliable answer from the material available."
        )

        result = main._basic_inquiry_provider_exhaustion_response(
            "What is a library?",
            {},
            {},
            recommendation_available=False,
        )

        provider_recovery.assert_called_once()
        self.assertNotEqual(
            result.get("provider"),
            "bounded_foundation_provider_exhaustion_recovery",
        )


if __name__ == "__main__":
    unittest.main()
