"""Tests for explicit, evidence-linked CLSS contextual comparison."""
from __future__ import annotations

import unittest

from clss_contextual_review import ContextualReviewError, compose_contextual_review


EVIDENCE = [
    {"evidence_id": "ev-obligation", "dimension": "commitment", "source_type": "self_report", "answer_text": "Responsibility is to invite questions."},
    {"evidence_id": "ev-conduct", "dimension": "conduct", "source_type": "first_hand_observation", "answer_text": "Discussion ended before concerns could be raised."},
    {"evidence_id": "ev-effect", "dimension": "consequences", "source_type": "documented_outcome", "answer_text": "The team did not know what had been decided."},
    {"evidence_id": "ev-context", "dimension": "unknown", "source_type": "unknown", "answer_text": "The time available is not yet known."},
    {"evidence_id": "ev-repair", "dimension": "correction", "source_type": "documented_outcome", "answer_text": "The decision was later reviewed."},
]


def review(**overrides):
    data = {
        "obligation_evidence_ids": ["ev-obligation"],
        "conduct_evidence_ids": ["ev-conduct"],
        "effect_evidence_ids": ["ev-effect"],
        "counterevidence_ids": [],
        "context_evidence_ids": [],
        "repair_evidence_ids": [],
        "source_conflict_evidence_ids": [],
        "alignment": "supports_tension",
        "context_status": "not_material",
        "repair_status": "no_repair_evidence",
        "source_status": "consistent",
        "rationale": "The stated service obligation and the described conduct appear to conflict, and the reported effect is linked to that episode.",
        "next_action": "Review the episode with affected participants and establish what prevented questions from being raised.",
        "next_action_owner": "Relevant participants",
        "observable_indicators": ["The meeting record captures the decision, questions, and follow-up."],
    }
    data.update(overrides)
    return data


class CLSSContextualReviewTests(unittest.TestCase):
    def test_explicit_supported_tension_requires_obligation_conduct_and_effect(self):
        result = compose_contextual_review(EVIDENCE, review(), mode="self")
        self.assertEqual(result["central_incoherence"]["finding_type"], "supported_tension")
        self.assertEqual(set(result["central_incoherence"]["evidence_ids"]), {"ev-obligation", "ev-conduct", "ev-effect"})
        self.assertEqual(result["path"], "deterministic_fallback")

    def test_missing_conduct_evidence_fails_to_insufficient(self):
        result = compose_contextual_review(
            EVIDENCE, review(conduct_evidence_ids=[]), mode="self"
        )
        self.assertEqual(result["central_incoherence"]["finding_type"], "insufficient_evidence")

    def test_material_context_keeps_finding_mixed(self):
        result = compose_contextual_review(
            EVIDENCE,
            review(context_status="material", context_evidence_ids=["ev-context"]),
            mode="third_party",
        )
        self.assertEqual(result["central_incoherence"]["finding_type"], "mixed_evidence")
        self.assertIn("private intent remains unknown", result["why_it_matters"]["text"])

    def test_alignment_without_defensible_tension_is_not_invented(self):
        result = compose_contextual_review(
            EVIDENCE, review(alignment="aligns"), mode="self"
        )
        self.assertEqual(result["central_incoherence"]["finding_type"], "no_defensible_tension")

    def test_conflicting_sources_remain_mixed(self):
        result = compose_contextual_review(
            EVIDENCE,
            review(source_status="conflict", source_conflict_evidence_ids=["ev-conduct", "ev-context"]),
            mode="third_party",
        )
        self.assertEqual(result["central_incoherence"]["finding_type"], "mixed_evidence")
        self.assertIn("conflicting accounts remain unresolved", result["what_could_change_the_interpretation"][0]["text"])

    def test_unknown_evidence_reference_is_rejected(self):
        with self.assertRaisesRegex(ContextualReviewError, "unknown evidence ID"):
            compose_contextual_review(
                EVIDENCE, review(obligation_evidence_ids=["ev-ghost"]), mode="self"
            )

    def test_invalid_alignment_is_rejected(self):
        with self.assertRaisesRegex(ContextualReviewError, "alignment must be"):
            compose_contextual_review(EVIDENCE, review(alignment="probably"), mode="self")


if __name__ == "__main__":
    unittest.main()
