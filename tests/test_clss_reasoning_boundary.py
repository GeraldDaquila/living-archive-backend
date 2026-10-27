"""Tests for the provider-neutral CLSS reasoning boundary."""
from __future__ import annotations

import unittest

from clss_reasoning_boundary import resolve_clss_response


EVIDENCE = [
    {
        "evidence_id": "ev-1",
        "dimension": "conduct",
        "source_type": "first_hand_observation",
        "answer_text": "A concrete action was observed.",
    }
]


def valid_candidate(evidence, mode):
    return {
        "mode": mode,
        "path": "llm",
        "central_incoherence": {
            "text": "The evidence supplied is not enough to establish a final coherence finding.",
            "finding_type": "insufficient_evidence",
            "evidence_ids": ["ev-1"],
        },
        "why_it_matters": {
            "text": "Context is needed to compare conduct with the relevant obligation.",
            "evidence_ids": ["ev-1"],
        },
        "what_the_evidence_says": [
            {"text": "A concrete action was described.", "evidence_ids": ["ev-1"]}
        ],
        "what_could_change_the_interpretation": [
            {"text": "The applicable responsibility and surrounding context could change the interpretation.", "evidence_ids": ["ev-1"]}
        ],
        "what_to_do_next": {
            "action": "Record the responsibility, action, effect, and relevant context for review.",
            "owner": None,
            "observable_indicators": ["The episode and its source are recorded."],
        },
        "limits": ["This response does not establish a final coherence finding."],
    }


class CLSSReasoningBoundaryTests(unittest.TestCase):
    def test_valid_candidate_is_returned_only_after_validation(self):
        result = resolve_clss_response(EVIDENCE, mode="self", candidate_builder=valid_candidate)
        self.assertEqual(result["path"], "llm")
        self.assertEqual(result["central_incoherence"]["evidence_ids"], ["ev-1"])

    def test_invalid_candidate_uses_validated_fallback(self):
        def invalid_builder(evidence, mode):
            return {"mode": mode, "path": "llm", "central_incoherence": {"text": "unsupported"}}
        result = resolve_clss_response(EVIDENCE, mode="self", candidate_builder=invalid_builder)
        self.assertEqual(result["path"], "deterministic_fallback")
        self.assertEqual(result["central_incoherence"]["finding_type"], "insufficient_evidence")

    def test_builder_exception_uses_validated_fallback(self):
        def broken_builder(evidence, mode):
            raise RuntimeError("secret/internal error must not escape")
        result = resolve_clss_response(EVIDENCE, mode="self", candidate_builder=broken_builder)
        self.assertEqual(result["path"], "deterministic_fallback")
        self.assertNotIn("secret/internal error", str(result))

    def test_no_builder_uses_fallback_without_network(self):
        result = resolve_clss_response(EVIDENCE, mode="third_party")
        self.assertEqual(result["path"], "deterministic_fallback")
        self.assertIn("does not establish a defensible conclusion", result["central_incoherence"]["text"])

    def test_empty_evidence_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_clss_response([], mode="self", candidate_builder=valid_candidate)


if __name__ == "__main__":
    unittest.main()
