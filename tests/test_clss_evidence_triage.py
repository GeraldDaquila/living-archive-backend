"""Behavioral tests for conservative CLSS evidence triage.

These tests exercise the triage implementation itself. They intentionally do not
claim to test semantic coherence reasoning or production visitor behavior.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.clss_evidence_triage import triage_evidence

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "clss" / "stewardship-coherence-cases.json"
)


class CLSSDeterministicEvidenceTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
        cls.by_id = {case["id"]: case for case in cls.cases}

    def triage_case(self, case_id):
        case = self.by_id[case_id]
        return triage_evidence(
            case.get("evidence", []),
            mode=case["mode"],
            missing_dimensions=case.get("missing_dimensions", []),
        )

    def test_labels_only_are_insufficient(self):
        result = self.triage_case("insufficient-evidence-labels-only")
        self.assertEqual(result["triage_type"], "insufficient_evidence")
        self.assertEqual(result["evidence_ids"], ["ev-label"])
        self.assertFalse(result["is_final_coherence_finding"])

    def test_silence_and_unknown_dimension_are_not_adverse(self):
        result = self.triage_case("third-party-intent-unknown")
        self.assertEqual(result["triage_type"], "insufficient_evidence")
        self.assertIn("ev-silence", result["evidence_ids"])
        self.assertTrue(any("private intent" in item for item in result["limitations"]))

    def test_missing_answers_are_explicit_gaps(self):
        result = self.triage_case("missing-answer-is-not-adverse")
        self.assertEqual(result["triage_type"], "insufficient_evidence")
        self.assertEqual(result["missing_dimensions"], ["accountability", "consequences"])
        self.assertNotIn("accountability", result["evidence_ids"])

    def test_repair_and_conflicting_sources_are_flagged_as_mixed(self):
        repair = self.triage_case("mixed-evidence-with-repair")
        conflict = self.triage_case("conflicting-source-provenance")
        self.assertEqual(repair["triage_type"], "mixed_evidence")
        self.assertEqual(conflict["triage_type"], "mixed_evidence")
        self.assertIn("ev-repair", repair["evidence_ids"])
        self.assertIn("ev-rumor", conflict["evidence_ids"])

    def test_strong_tension_is_not_invented_by_keyword_matching(self):
        result = self.triage_case("strong-supported-tension")
        self.assertEqual(result["triage_type"], "insufficient_evidence")
        self.assertFalse(result["is_final_coherence_finding"])
        self.assertIn("contextual comparison", result["reason"])

    def test_time_critical_case_is_not_misclassified_as_a_finding(self):
        result = self.triage_case("time-critical-context")
        self.assertFalse(result["is_final_coherence_finding"])
        self.assertEqual(result["triage_type"], "insufficient_evidence")

    def test_duplicate_ids_fail_closed(self):
        evidence = [
            {"evidence_id": "same", "dimension": "conduct", "source_type": "first_hand_observation", "answer_text": "Observed action"},
            {"evidence_id": "same", "dimension": "correction", "source_type": "documented_outcome", "answer_text": "Later correction"},
        ]
        with self.assertRaisesRegex(ValueError, "unique"):
            triage_evidence(evidence, mode="self")

    def test_invalid_mode_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "mode"):
            triage_evidence([], mode="unspecified")


if __name__ == "__main__":
    unittest.main()
