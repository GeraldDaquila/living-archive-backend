"""Executable integrity and safety-contract tests for CLSS design fixtures.

These tests validate fixture structure and machine-checkable invariants. They do
not claim to evaluate natural-language reasoning quality or production behavior.
Run with: python -m unittest tests/test_clss_stewardship_fixtures.py -v
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "clss"
    / "stewardship-coherence-cases.json"
)
ALLOWED_MODES = {"self", "third_party"}
ALLOWED_DIMENSIONS = {
    "commitment", "conduct", "consequences", "coherence",
    "accountability", "counterevidence", "correction", "unknown",
}
ALLOWED_SOURCE_TYPES = {
    "self_report", "first_hand_observation", "documented_outcome",
    "second_hand_report", "interpretation", "unknown",
}
ALLOWED_FINDINGS = {
    "supported_tension", "mixed_evidence",
    "insufficient_evidence", "no_defensible_tension",
}
REQUIRED_CASE_IDS = {
    "strong-supported-tension",
    "mixed-evidence-with-repair",
    "time-critical-context",
    "insufficient-evidence-labels-only",
    "no-defensible-tension",
    "conflicting-source-provenance",
    "third-party-intent-unknown",
    "missing-answer-is-not-adverse",
    "llm-invalid-output-fallback",
}


def load_fixture_document():
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


class StewardshipFixtureIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_fixture_document()
        cls.cases = cls.document.get("cases", [])
        cls.by_id = {case.get("id"): case for case in cls.cases}

    def test_fixture_document_declares_design_only_status(self):
        self.assertEqual(self.document.get("schema_version"), "1.0")
        self.assertEqual(self.document.get("status"), "design_fixtures")
        self.assertIn("integrity suite", self.document.get("note", ""))
        self.assertIn("does not yet test semantic reasoning", self.document.get("note", ""))

    def test_all_required_regression_scenarios_exist_once(self):
        ids = [case.get("id") for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)), "Fixture IDs must be unique")
        self.assertEqual(set(ids), REQUIRED_CASE_IDS)

    def test_each_case_has_valid_mode_and_safety_expectations(self):
        for case in self.cases:
            with self.subTest(case=case.get("id")):
                self.assertIn(case.get("mode"), ALLOWED_MODES)
                self.assertTrue(case.get("must_preserve"))
                self.assertTrue(case.get("must_not"))
                self.assertIsInstance(case.get("must_preserve"), list)
                self.assertIsInstance(case.get("must_not"), list)

    def test_evidence_ids_are_unique_and_referenced_ids_exist(self):
        for case in self.cases:
            with self.subTest(case=case.get("id")):
                evidence = case.get("evidence", [])
                ids = [item.get("evidence_id") for item in evidence]
                self.assertEqual(len(ids), len(set(ids)), "Evidence IDs must be unique")
                self.assertTrue(all(isinstance(value, str) and value for value in ids))
                for item in evidence:
                    self.assertIn(item.get("dimension"), ALLOWED_DIMENSIONS)
                    self.assertIn(item.get("source_type"), ALLOWED_SOURCE_TYPES)
                    self.assertIsInstance(item.get("answer_text"), str)
                    self.assertTrue(item["answer_text"].strip())

                required = set(case.get("must_include_evidence_ids", []))
                self.assertTrue(
                    required.issubset(set(ids)),
                    f"Expected evidence IDs missing from input: {required - set(ids)}",
                )

    def test_expected_finding_types_are_from_contract(self):
        for case in self.cases:
            with self.subTest(case=case.get("id")):
                if "expected_finding_type" in case:
                    self.assertIn(case["expected_finding_type"], ALLOWED_FINDINGS)

    def test_missing_dimensions_are_not_misrepresented_as_evidence(self):
        case = self.by_id["missing-answer-is-not-adverse"]
        evidence_dimensions = {item["dimension"] for item in case.get("evidence", [])}
        missing = set(case.get("missing_dimensions", []))
        self.assertTrue(missing)
        self.assertTrue(missing.isdisjoint(evidence_dimensions))
        self.assertEqual(case["expected_finding_type"], "insufficient_evidence")
        self.assertTrue(
            any("not adverse" in rule for rule in case["must_not"]),
            "Missing answers must explicitly be protected from adverse inference",
        )

    def test_third_party_silence_does_not_claim_private_intent(self):
        case = self.by_id["third-party-intent-unknown"]
        self.assertEqual(case["mode"], "third_party")
        self.assertEqual(case["expected_finding_type"], "insufficient_evidence")
        self.assertTrue(
            any("infer consent" in rule for rule in case["must_not"])
        )
        self.assertTrue(
            any("inner commitment" in rule for rule in case["must_not"])
        )

    def test_contextual_urgency_case_does_not_prejudge_conduct(self):
        case = self.by_id["time-critical-context"]
        self.assertEqual(case["expected_finding_type"], "no_defensible_tension")
        self.assertTrue(
            any("time constraint" in phrase for phrase in case["must_preserve"])
        )
        self.assertTrue(
            any("unilateral action alone" in rule for rule in case["must_not"])
        )

    def test_invalid_llm_case_contains_a_deliberately_invalid_reference(self):
        case = self.by_id["llm-invalid-output-fallback"]
        supplied = set(case.get("input_evidence_ids", []))
        output = case.get("invalid_llm_output", {})
        candidate = output.get("central_incoherence", {})
        cited = set(candidate.get("evidence_ids", []))
        self.assertTrue(supplied)
        self.assertTrue(cited)
        self.assertTrue(cited.isdisjoint(supplied))
        self.assertEqual(
            case.get("expected_system_behavior"),
            "reject_llm_output_and_use_deterministic_fallback",
        )

    def test_labels_only_case_is_not_accepted_as_a_supported_tension(self):
        case = self.by_id["insufficient-evidence-labels-only"]
        self.assertEqual(case["expected_finding_type"], "insufficient_evidence")
        self.assertTrue(
            any("concrete example" in phrase for phrase in case["must_preserve"])
        )
        self.assertTrue(
            any("invent a contradiction" in rule for rule in case["must_not"])
        )


if __name__ == "__main__":
    unittest.main()
