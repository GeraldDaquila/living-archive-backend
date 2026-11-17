"""Regression coverage for provider-exhaustion answer recovery in The Guide."""

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

    @patch("main._basic_inquiry_round1_deterministic_response")
    def test_reflective_conceptual_question_survives_full_provider_exhaustion_boundary(
        self, deterministic_response
    ):
        deterministic_response.return_value = {
            "response": "I couldn't verify a reliable answer from the material available.",
            "doorway_title": "",
            "provider": "deterministic_question_preserving_recovery",
            "model": "",
        }

        result = main._basic_inquiry_provider_exhaustion_response(
            "How can hope be disciplined rather than naïve?",
            {},
            {},
            recommendation_available=False,
        )

        answer = result["response"]
        self.assertEqual(result["provider"], "bounded_provider_exhaustion_recovery")
        self.assertEqual(len(answer.split("\n\n")), 3)
        self.assertTrue(answer.startswith("Hope can be disciplined"))
        self.assertIn("uncertainty", answer.casefold())
        self.assertNotIn("Start by defining the outcome", answer)
        self.assertNotIn("responsibilities that cannot be lost", answer)

    @patch("main._basic_inquiry_round1_deterministic_response")
    def test_explicit_practical_question_keeps_practical_provider_exhaustion_recovery(
        self, deterministic_response
    ):
        deterministic_response.return_value = {
            "response": "I couldn't verify a reliable answer from the material available.",
            "doorway_title": "",
            "provider": "deterministic_question_preserving_recovery",
            "model": "",
        }

        result = main._basic_inquiry_provider_exhaustion_response(
            "How can an organization make a consequential change responsibly?",
            {},
            {},
            recommendation_available=False,
        )

        self.assertIn("Start by defining the outcome", result["response"])
        self.assertIn("compare realistic options", result["response"])


if __name__ == "__main__":
    unittest.main()


def test_algorithmic_bias_question_uses_mechanism_first_recovery():
    answer = main._compose_provider_exhaustion_recovery(
        "How can algorithmic systems scale existing biases or institutional failures?"
    )
    lowered = answer.casefold()
    assert "ranking system" in lowered
    assert "feedback loops" in lowered
    assert "not mean an algorithm is always the original cause" in lowered
    assert answer.count("\n\n") == 2

    @patch("main._basic_inquiry_round1_deterministic_response")
    def test_consequential_action_question_survives_full_provider_exhaustion_boundary(
        self, deterministic_response
    ):
        deterministic_response.return_value = {
            "response": "I couldn't verify a reliable answer from the material available.",
            "doorway_title": "",
            "provider": "deterministic_question_preserving_recovery",
            "model": "",
        }

        result = main._basic_inquiry_provider_exhaustion_response(
            "How should people act when the future is uncertain but consequential?",
            {},
            {},
            recommendation_available=False,
        )

        answer = result["response"]
        self.assertEqual(result["provider"], "bounded_provider_exhaustion_recovery")
        self.assertEqual(len(answer.split("\\n\\n")), 3)
        self.assertTrue(answer.startswith("When a decision has serious consequences"))
        self.assertIn("preserves room to learn and correct", answer)
        self.assertIn("signals for review", answer)
        self.assertIn("accountable", answer)
        self.assertNotIn("AI", answer)
        self.assertNotIn("civilizational", answer.casefold())
        self.assertNotIn("Distinguish strain and transition", answer)
