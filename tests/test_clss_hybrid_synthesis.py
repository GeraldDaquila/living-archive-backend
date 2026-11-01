"""Tests for the isolated CLSS hybrid-synthesis adapter."""
from __future__ import annotations

import unittest

from clss_hybrid_synthesis import (
    CONSENT_NOTICE_VERSION,
    CONSENT_PURPOSE,
    CLSSHybridSynthesisError,
    build_minimized_candidate_request,
    resolve_hybrid_candidate,
)

ANSWERS = [
    {"prompt_id": "responsibility-service", "answer_text": "I was responsible for coordinating the response.", "source_type": "self_report"},
    {"prompt_id": "concrete-episode", "answer_text": "I observed the schedule being changed.", "source_type": "first_hand_observation"},
    {"prompt_id": "consequences", "answer_text": "The team received the revised schedule.", "source_type": "documented_outcome"},
]
CONSENT = {
    "granted": True,
    "purpose": CONSENT_PURPOSE,
    "notice_version": CONSENT_NOTICE_VERSION,
}


def valid_candidate(request):
    ids = [item["evidence_id"] for item in request["evidence"]]
    return {
        "mode": request["mode"],
        "path": "llm",
        "central_incoherence": {
            "text": "The supplied accounts do not establish a settled conclusion; review the cited material with context.",
            "finding_type": "insufficient_evidence",
            "evidence_ids": ids,
        },
        "why_it_matters": {
            "text": "A fair review requires the responsibility, conduct, effects, and context to be considered together.",
            "evidence_ids": ids,
        },
        "what_the_evidence_says": [
            {"text": item["answer_text"], "evidence_ids": [item["evidence_id"]]}
            for item in request["evidence"]
        ],
        "what_could_change_the_interpretation": [
            {"text": "Additional context or counterevidence may change this interpretation.", "evidence_ids": ids}
        ],
        "what_to_do_next": {
            "action": "Verify the episode and record relevant context before drawing a conclusion.",
            "owner": None,
            "observable_indicators": ["The source and context for each account are recorded."],
        },
        "limits": ["This candidate is not a suitability decision and requires human semantic review."],
    }


class CLSSHybridSynthesisTests(unittest.TestCase):
    def test_no_consent_never_calls_candidate_builder(self):
        called = []
        result = resolve_hybrid_candidate(
            ANSWERS, mode="self", consent=None,
            candidate_builder=lambda request: called.append(request),
        )
        self.assertEqual(called, [])
        self.assertFalse(result["provider_invoked"])
        self.assertEqual(result["path"], "deterministic_fallback")

    def test_wrong_purpose_or_notice_is_rejected(self):
        normalized = __import__("clss_evidence_normalization").normalize_questionnaire_answers(ANSWERS, mode="self")
        for consent in (
            {"granted": True, "purpose": "other", "notice_version": CONSENT_NOTICE_VERSION},
            {"granted": True, "purpose": CONSENT_PURPOSE, "notice_version": "old"},
            {"granted": "true", "purpose": CONSENT_PURPOSE, "notice_version": CONSENT_NOTICE_VERSION},
        ):
            with self.subTest(consent=consent):
                with self.assertRaises(CLSSHybridSynthesisError):
                    build_minimized_candidate_request(normalized, consent=consent)

    def test_payload_is_minimized_and_does_not_copy_optional_context(self):
        enriched = [dict(item, context=["unnecessary free text"], affected_parties=["named person"]) for item in ANSWERS]
        normalized = __import__("clss_evidence_normalization").normalize_questionnaire_answers(enriched, mode="self")
        payload = build_minimized_candidate_request(normalized, consent=CONSENT)
        self.assertEqual(set(payload["evidence"][0]), {
            "evidence_id", "prompt_id", "dimension", "source_type", "answer_text", "provenance"
        })
        self.assertNotIn("context", payload["evidence"][0])
        self.assertNotIn("affected_parties", payload["evidence"][0])

    def test_answer_size_limits_fail_closed(self):
        oversized = [dict(ANSWERS[0], answer_text="x" * 4001)]
        normalized = __import__("clss_evidence_normalization").normalize_questionnaire_answers(oversized, mode="self")
        with self.assertRaises(CLSSHybridSynthesisError):
            build_minimized_candidate_request(normalized, consent=CONSENT)

    def test_valid_candidate_is_unverified_and_requires_human_review(self):
        result = resolve_hybrid_candidate(
            ANSWERS, mode="self", consent=CONSENT, candidate_builder=valid_candidate
        )
        self.assertEqual(result["path"], "llm")
        self.assertEqual(result["semantic_status"], "unverified_candidate")
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["transmission_performed"])

    def test_invalid_reference_uses_deterministic_fallback(self):
        def invalid(request):
            candidate = valid_candidate(request)
            candidate["central_incoherence"]["evidence_ids"] = ["invented-id"]
            return candidate
        result = resolve_hybrid_candidate(
            ANSWERS, mode="self", consent=CONSENT, candidate_builder=invalid
        )
        self.assertEqual(result["path"], "deterministic_fallback")
        self.assertFalse(result["human_review_required"])

    def test_third_party_mode_is_preserved_and_motive_is_prohibited(self):
        result = resolve_hybrid_candidate(
            ANSWERS, mode="third_party", consent=CONSENT, candidate_builder=valid_candidate
        )
        self.assertEqual(result["response"]["mode"], "third_party")
        self.assertTrue(result["human_review_required"])

    def test_no_evidence_does_not_manufacture_a_finding(self):
        with self.assertRaises(CLSSHybridSynthesisError):
            resolve_hybrid_candidate([], mode="self", consent=CONSENT, candidate_builder=valid_candidate)


if __name__ == "__main__":
    unittest.main()
