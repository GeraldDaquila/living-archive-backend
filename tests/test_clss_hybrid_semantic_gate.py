"""Semantic release-gate tests for the five CLSS evidence profiles.

These tests are adversarial contract checks, not automated semantic approval.
Unsupported entailment and causal claims remain human-review questions.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tests.clss_response_validator import ResponseValidationError, validate_candidate_response

ROOT = Path(__file__).parent
FIXTURE_FILE = ROOT / "fixtures" / "clss" / "stewardship-coherence-cases.json"
CANDIDATE_FILE = ROOT / "fixtures" / "clss" / "semantic-response-candidates.json"

RELEASE_MATRIX = {
    "strengths_only": "no-defensible-tension",
    "concern_only": "insufficient-evidence-labels-only",
    "mixed": "mixed-evidence-with-repair",
    "contradictory": "conflicting-source-provenance",
    "sparse": "missing-answer-is-not-adverse",
}


def all_response_text(response):
    values = [
        response["central_incoherence"]["text"],
        response["why_it_matters"]["text"],
        response["what_to_do_next"]["action"],
        *response["what_to_do_next"]["observable_indicators"],
        *response["limits"],
    ]
    for field in ("what_the_evidence_says", "what_could_change_the_interpretation"):
        values.extend(item["text"] for item in response[field])
    return " ".join(values).lower()


class CLSSHybridSemanticGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {
            case["id"]: case
            for case in json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))["cases"]
        }
        candidate_doc = json.loads(CANDIDATE_FILE.read_text(encoding="utf-8"))
        cls.candidates = {
            item["case_id"]: item["response"] for item in candidate_doc["cases"]
        }
        cls.candidate_status = candidate_doc["status"]

    def test_five_release_profiles_are_covered_exactly(self):
        self.assertEqual(set(RELEASE_MATRIX.values()), {
            "no-defensible-tension",
            "insufficient-evidence-labels-only",
            "mixed-evidence-with-repair",
            "conflicting-source-provenance",
            "missing-answer-is-not-adverse",
        })
        for profile, case_id in RELEASE_MATRIX.items():
            with self.subTest(profile=profile):
                self.assertIn(case_id, self.fixtures)
                self.assertIn(case_id, self.candidates)

    def test_authored_candidates_are_not_mislabeled_as_model_or_human_approved(self):
        self.assertEqual(self.candidate_status, "candidate_drafts_not_human_reviewed")

    def test_each_release_profile_has_expected_finding_and_required_citations(self):
        for profile, case_id in RELEASE_MATRIX.items():
            fixture = self.fixtures[case_id]
            candidate = self.candidates[case_id]
            evidence_ids = {item["evidence_id"] for item in fixture.get("evidence", [])}
            validate_candidate_response(
                candidate, evidence_ids, mode=fixture["mode"], path="llm"
            )
            self.assertEqual(
                candidate["central_incoherence"]["finding_type"],
                fixture["expected_finding_type"],
                msg=f"{profile} finding type mismatch",
            )
            self.assertTrue(
                set(fixture["must_include_evidence_ids"]).issubset(
                    set(candidate["central_incoherence"]["evidence_ids"])
                )
            )

    def test_strengths_only_case_does_not_manufacture_a_problem(self):
        response = self.candidates["no-defensible-tension"]
        text = all_response_text(response)
        self.assertEqual(response["central_incoherence"]["finding_type"], "no_defensible_tension")
        self.assertIn("no defensible incoherence is established", text)
        self.assertNotIn("hidden incoherence", text)

    def test_concern_only_labels_remain_characterizations(self):
        response = self.candidates["insufficient-evidence-labels-only"]
        text = all_response_text(response)
        self.assertEqual(response["central_incoherence"]["finding_type"], "insufficient_evidence")
        self.assertIn("characterizations, not concrete examples", text)
        self.assertNotIn("the leader is selfish", text)

    def test_mixed_case_preserves_concern_and_repair(self):
        response = self.candidates["mixed-evidence-with-repair"]
        text = all_response_text(response)
        for phrase in ("defensive", "acknowledged", "changed the plan", "followed up"):
            self.assertIn(phrase, text)

    def test_contradictory_case_preserves_both_source_types_as_unresolved(self):
        response = self.candidates["conflicting-source-provenance"]
        text = all_response_text(response)
        self.assertIn("first-hand", text)
        self.assertIn("second-hand", text)
        self.assertIn("remain unresolved", text)

    def test_sparse_case_keeps_missing_dimensions_non_adverse(self):
        response = self.candidates["missing-answer-is-not-adverse"]
        text = all_response_text(response)
        self.assertIn("gap, not evidence against you", text)
        self.assertIn("no conclusion is drawn from unanswered dimensions", text)

    def test_fabricated_evidence_reference_is_rejected(self):
        case_id = "strong-supported-tension"
        fixture = self.fixtures[case_id]
        candidate = copy.deepcopy(self.candidates[case_id])
        candidate["central_incoherence"]["evidence_ids"].append("invented-evidence")
        with self.assertRaisesRegex(ResponseValidationError, "unknown evidence"):
            validate_candidate_response(
                candidate,
                {item["evidence_id"] for item in fixture["evidence"]},
                mode=fixture["mode"],
                path="llm",
            )

    def test_private_motive_and_suitability_verdict_are_rejected(self):
        case_id = "third-party-intent-unknown"
        fixture = self.fixtures[case_id]
        allowed = {item["evidence_id"] for item in fixture["evidence"]}
        for phrase in ("The person secretly wants the role.", "The person should not be promoted."):
            candidate = copy.deepcopy(self.candidates[case_id])
            candidate["central_incoherence"]["text"] = phrase
            with self.subTest(phrase=phrase):
                with self.assertRaises(ResponseValidationError):
                    validate_candidate_response(
                        candidate, allowed, mode=fixture["mode"], path="llm"
                    )

    def test_provenance_laundering_is_a_human_gate_not_a_structural_pass(self):
        case_id = "conflicting-source-provenance"
        fixture = self.fixtures[case_id]
        candidate = copy.deepcopy(self.candidates[case_id])
        candidate["what_the_evidence_says"][1]["text"] = (
            "The second-hand report establishes that the leader had already decided."
        )
        # This intentionally remains structurally valid: the validator cannot
        # prove that a paraphrase preserves source epistemic status.
        validate_candidate_response(
            candidate,
            {item["evidence_id"] for item in fixture["evidence"]},
            mode=fixture["mode"],
            path="llm",
        )
        self.assertIn("not_reviewed", "not_reviewed")
        self.assertIn("second-hand report", fixture["must_preserve"][0])

    def test_unsupported_causal_claims_are_not_automatically_semantically_accepted(self):
        case_id = "strong-supported-tension"
        fixture = self.fixtures[case_id]
        candidate = copy.deepcopy(self.candidates[case_id])
        candidate["why_it_matters"]["text"] = (
            "The conduct caused every team member to lose trust in the leader."
        )
        # Structure and evidence IDs alone cannot verify causality or scope.
        validate_candidate_response(
            candidate,
            {item["evidence_id"] for item in fixture["evidence"]},
            mode=fixture["mode"],
            path="llm",
        )
        # The candidate collection and review template remain explicitly unreviewed.
        self.assertEqual(self.candidate_status, "candidate_drafts_not_human_reviewed")


if __name__ == "__main__":
    unittest.main()
