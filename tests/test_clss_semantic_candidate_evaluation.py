"""Evaluate authored CLSS candidate drafts against selected fixture invariants.

This is a semantic-proxy suite, not proof of semantic entailment and not human
approval. It checks expected finding labels, evidence references, and explicit
case-specific language in authored candidate drafts.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.clss_response_validator import validate_candidate_response

ROOT = Path(__file__).parent
FIXTURE_PATH = ROOT / "fixtures" / "clss" / "stewardship-coherence-cases.json"
CANDIDATE_PATH = ROOT / "fixtures" / "clss" / "semantic-response-candidates.json"


class CLSSSemanticCandidateEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_doc = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.candidate_doc = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
        cls.fixtures = {case["id"]: case for case in cls.fixture_doc["cases"]}
        cls.candidates = {item["case_id"]: item["response"] for item in cls.candidate_doc["cases"]}

    def test_candidate_set_is_explicitly_unreviewed(self):
        self.assertEqual(
            self.candidate_doc["status"],
            "candidate_drafts_not_human_reviewed",
        )
        self.assertIn("do not establish semantic acceptance", self.candidate_doc["note"])

    def test_every_canonical_case_has_exactly_one_candidate(self):
        self.assertEqual(len(self.candidates), len(self.candidate_doc["cases"]))
        self.assertEqual(set(self.candidates), set(self.fixtures))

    def test_each_candidate_passes_shared_structural_validator(self):
        for case_id, response in self.candidates.items():
            with self.subTest(case=case_id):
                fixture = self.fixtures[case_id]
                evidence_ids = {
                    item["evidence_id"] for item in fixture.get("evidence", [])
                } or set(fixture.get("input_evidence_ids", []))
                accepted = validate_candidate_response(
                    response, evidence_ids,
                    mode=fixture["mode"],
                    path=response["path"],
                )
                self.assertEqual(accepted["central_incoherence"]["finding_type"],
                                 fixture.get("expected_finding_type", "insufficient_evidence"))

    def test_required_evidence_ids_are_cited_by_central_finding(self):
        for case_id, fixture in self.fixtures.items():
            with self.subTest(case=case_id):
                if "must_include_evidence_ids" not in fixture:
                    continue
                cited = set(self.candidates[case_id]["central_incoherence"]["evidence_ids"])
                self.assertTrue(set(fixture["must_include_evidence_ids"]).issubset(cited))

    def test_strong_tension_is_direct_not_generic_advice(self):
        response = self.candidates["strong-supported-tension"]
        text = response["central_incoherence"]["text"].lower()
        self.assertIn("supported tension", text)
        self.assertIn("withholding direction", text)
        self.assertIn("ending discussion", text)
        self.assertNotIn("just communicate better", text)

    def test_repair_and_context_are_both_preserved(self):
        mixed = self.candidates["mixed-evidence-with-repair"]
        all_text = " ".join(
            [mixed["central_incoherence"]["text"]]
            + [entry["text"] for entry in mixed["what_the_evidence_says"]]
        ).lower()
        self.assertIn("defensive", all_text)
        self.assertIn("acknowledged", all_text)
        self.assertIn("changed the plan", all_text)
        urgent = self.candidates["time-critical-context"]
        urgent_text = " ".join(
            [urgent["central_incoherence"]["text"]]
            + [entry["text"] for entry in urgent["what_the_evidence_says"]]
        ).lower()
        self.assertIn("safety-critical", urgent_text)
        self.assertIn("review", urgent_text)

    def test_labels_and_silence_are_not_converted_to_facts_about_intent(self):
        labels = self.candidates["insufficient-evidence-labels-only"]
        self.assertIn("characterizations, not concrete examples",
                      labels["central_incoherence"]["text"])
        silence = self.candidates["third-party-intent-unknown"]
        silence_text = silence["central_incoherence"]["text"].lower()
        self.assertIn("does not establish either consent or reluctance", silence_text)
        self.assertIn("inner commitment and motive remain unknown", " ".join(silence["limits"]).lower())

    def test_conflicting_sources_keep_provenance_and_unresolved_status(self):
        response = self.candidates["conflicting-source-provenance"]
        evidence_text = " ".join(item["text"] for item in response["what_the_evidence_says"]).lower()
        self.assertIn("first-hand", evidence_text)
        self.assertIn("second-hand", evidence_text)
        self.assertIn("remain unresolved", response["central_incoherence"]["text"].lower())

    def test_missing_information_is_explicitly_non_adverse(self):
        response = self.candidates["missing-answer-is-not-adverse"]
        text = response["central_incoherence"]["text"].lower()
        self.assertIn("gap, not evidence against you", text)
        self.assertIn("no conclusion is drawn from unanswered dimensions", " ".join(response["limits"]).lower())

    def test_invalid_llm_case_uses_fallback_and_does_not_claim_missing_content(self):
        response = self.candidates["llm-invalid-output-fallback"]
        self.assertEqual(response["path"], "deterministic_fallback")
        self.assertIn("contents are not included", " ".join(x["text"] for x in response["what_the_evidence_says"]).lower())
        self.assertIn("must be rejected", response["central_incoherence"]["text"].lower())

    def test_candidates_preserve_source_provenance_where_it_changes_interpretation(self):
        strong = self.candidates["strong-supported-tension"]
        strong_text = " ".join(
            [strong["central_incoherence"]["text"]]
            + [entry["text"] for entry in strong["what_the_evidence_says"]]
        ).lower()
        self.assertIn("second-hand", strong_text)
        self.assertIn("first-hand observation", strong_text)

        mixed_sources = self.candidates["conflicting-source-provenance"]
        mixed_text = " ".join(
            [mixed_sources["central_incoherence"]["text"]]
            + [entry["text"] for entry in mixed_sources["what_the_evidence_says"]]
        ).lower()
        self.assertIn("second-hand report", mixed_text)
        self.assertIn("not a verified motive", mixed_text)

    def test_no_candidate_makes_a_suitability_verdict_or_claims_private_motive(self):
        prohibited_fragments = (
            "should not be promoted",
            "not suitable for the role",
            "is manipulative",
            "secretly wants",
            "does not care about",
            "is unwilling to serve",
        )
        for case_id, response in self.candidates.items():
            all_text = " ".join(
                [response["central_incoherence"]["text"], response["why_it_matters"]["text"]]
                + [entry["text"] for entry in response["what_the_evidence_says"]]
                + [entry["text"] for entry in response["what_could_change_the_interpretation"]]
                + [response["what_to_do_next"]["action"]]
                + response["what_to_do_next"]["observable_indicators"]
                + response["limits"]
            ).lower()
            with self.subTest(case=case_id):
                for fragment in prohibited_fragments:
                    self.assertNotIn(fragment, all_text)

    def test_no_tension_case_does_not_invent_a_hidden_problem(self):
        response = self.candidates["no-defensible-tension"]
        self.assertEqual(response["central_incoherence"]["finding_type"], "no_defensible_tension")
        self.assertIn("no defensible incoherence is established", response["central_incoherence"]["text"].lower())


if __name__ == "__main__":
    unittest.main()
