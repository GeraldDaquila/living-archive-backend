"""Unit tests for the CLSS canonical response validator."""
import unittest

from tests.clss_response_validator import (
    ResponseValidationError,
    validate_candidate_response,
    validate_or_fallback,
)


EVIDENCE = {"ev-commit", "ev-conduct", "ev-impact"}


def valid_response():
    return {
        "mode": "third_party",
        "path": "deterministic_fallback",
        "central_incoherence": {
            "text": "The reported commitment to involve the team conflicts with described meetings where discussion was ended before concerns could be raised.",
            "finding_type": "supported_tension",
            "evidence_ids": ["ev-commit", "ev-conduct"],
        },
        "why_it_matters": {
            "text": "Team members reportedly became unsure what had been decided.",
            "evidence_ids": ["ev-impact"],
        },
        "what_the_evidence_says": [
            {
                "text": "The commitment is second-hand, while the conduct is described as a first-hand observation.",
                "evidence_ids": ["ev-commit", "ev-conduct"],
            }
        ],
        "what_could_change_the_interpretation": [
            {
                "text": "A concrete example of a time-sensitive meeting could clarify whether the discussion limit was proportionate.",
                "evidence_ids": ["ev-conduct"],
            }
        ],
        "what_to_do_next": {
            "action": "Review one specific meeting with the leader and affected colleagues, comparing the intended decision process with what occurred.",
            "owner": "Visitor and leader jointly",
            "observable_indicators": [
                "The leader states the decision, rationale, and time constraints.",
                "Colleagues can identify how and when concerns may be raised.",
            ],
        },
        "limits": [
            "The available reports do not establish the leader's private motive."
        ],
    }


class CandidateResponseValidatorTests(unittest.TestCase):
    def test_accepts_well_formed_evidence_linked_response(self):
        result = validate_candidate_response(
            valid_response(), EVIDENCE, mode="third_party", path="deterministic_fallback"
        )
        self.assertEqual(result["central_incoherence"]["finding_type"], "supported_tension")

    def test_rejects_unknown_evidence_reference(self):
        response = valid_response()
        response["central_incoherence"]["evidence_ids"] = ["ev-ghost"]
        with self.assertRaisesRegex(ResponseValidationError, "unknown evidence"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_rejects_supported_tension_without_evidence(self):
        response = valid_response()
        response["central_incoherence"]["evidence_ids"] = []
        with self.assertRaisesRegex(ResponseValidationError, "must cite at least one"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_rejects_mode_mismatch(self):
        response = valid_response()
        response["mode"] = "self"
        with self.assertRaisesRegex(ResponseValidationError, "does not match"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_rejects_missing_observable_indicators(self):
        response = valid_response()
        response["what_to_do_next"]["observable_indicators"] = []
        with self.assertRaisesRegex(ResponseValidationError, "at least one observable"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_rejects_third_party_private_intent_claim(self):
        response = valid_response()
        response["central_incoherence"]["text"] = "The leader secretly wants to silence colleagues."
        with self.assertRaisesRegex(ResponseValidationError, "private intent"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_rejects_suitability_verdict(self):
        response = valid_response()
        response["what_to_do_next"]["action"] = "He should not be promoted."
        with self.assertRaisesRegex(ResponseValidationError, "prohibited"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_rejects_extra_fields_instead_of_silently_ignoring_them(self):
        response = valid_response()
        response["score"] = 8
        with self.assertRaisesRegex(ResponseValidationError, "fields do not match"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_invalid_llm_candidate_selects_validated_fallback(self):
        candidate = valid_response()
        candidate["central_incoherence"]["evidence_ids"] = ["ev-not-in-input"]
        fallback = valid_response()
        fallback["path"] = "deterministic_fallback"
        accepted, path = validate_or_fallback(
            candidate, fallback, EVIDENCE, mode="third_party"
        )
        self.assertEqual(path, "deterministic_fallback")
        self.assertEqual(accepted["path"], "deterministic_fallback")

    def test_valid_llm_candidate_is_accepted(self):
        candidate = valid_response()
        candidate["path"] = "llm"
        fallback = valid_response()
        accepted, path = validate_or_fallback(
            candidate, fallback, EVIDENCE, mode="third_party"
        )
        self.assertEqual(path, "llm")
        self.assertEqual(accepted["path"], "llm")

    def test_invalid_candidate_and_invalid_fallback_fail_closed(self):
        candidate = valid_response()
        candidate["central_incoherence"]["evidence_ids"] = ["ev-not-in-input"]
        fallback = valid_response()
        fallback["central_incoherence"]["evidence_ids"] = ["ev-also-not-in-input"]
        with self.assertRaisesRegex(ResponseValidationError, "unknown evidence"):
            validate_or_fallback(candidate, fallback, EVIDENCE, mode="third_party")

    def test_rejects_evidence_summary_without_citations(self):
        response = valid_response()
        response["what_the_evidence_says"][0]["evidence_ids"] = []
        with self.assertRaisesRegex(ResponseValidationError, "must cite at least one"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_rejects_private_intent_claim_in_limits_section(self):
        response = valid_response()
        response["limits"] = ["The leader secretly wants to control the team."]
        with self.assertRaisesRegex(ResponseValidationError, "private intent"):
            validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")

    def test_no_defensible_tension_can_be_returned_without_forcing_a_finding(self):
        response = valid_response()
        response["central_incoherence"] = {
            "text": "The evidence provided currently aligns with the stated responsibility; no defensible tension is established.",
            "finding_type": "no_defensible_tension",
            "evidence_ids": ["ev-commit", "ev-conduct"],
        }
        accepted = validate_candidate_response(response, EVIDENCE, mode="third_party", path="deterministic_fallback")
        self.assertEqual(accepted["central_incoherence"]["finding_type"], "no_defensible_tension")

    def test_rejects_invalid_path(self):
        with self.assertRaisesRegex(ResponseValidationError, "response path is invalid"):
            validate_candidate_response(valid_response(), EVIDENCE, mode="third_party", path="provider_raw")


if __name__ == "__main__":
    unittest.main()
