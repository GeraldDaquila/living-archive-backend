"""Tests for the fixture-driven CLSS reasoning acceptance gate.

These tests verify the gate rejects incorrect labels and incomplete evidence
coverage. They do not claim that the sample candidate is a genuine model result.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.clss_reasoning_acceptance import (
    ReasoningAcceptanceError,
    validate_reasoning_candidate,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "clss" / "stewardship-coherence-cases.json"
)


def candidate_for(fixture, *, finding_type=None, central_ids=None):
    evidence = fixture.get("evidence", [])
    evidence_ids = [item["evidence_id"] for item in evidence]
    central_ids = evidence_ids if central_ids is None else central_ids
    return {
        "mode": fixture["mode"],
        "path": "llm",
        "central_incoherence": {
            "text": "The evidence supports the stated finding within the limits described.",
            "finding_type": finding_type or fixture["expected_finding_type"],
            "evidence_ids": central_ids,
        },
        "why_it_matters": {
            "text": "The interpretation should remain connected to the evidence supplied.",
            "evidence_ids": evidence_ids[:1],
        },
        "what_the_evidence_says": [
            {
                "text": "The supplied evidence and its provenance should be reviewed directly.",
                "evidence_ids": evidence_ids,
            }
        ],
        "what_could_change_the_interpretation": [
            {
                "text": "Additional concrete context could change the interpretation.",
                "evidence_ids": evidence_ids[:1],
            }
        ],
        "what_to_do_next": {
            "action": "Review the cited evidence with the people directly involved and record any correction or missing context.",
            "owner": "Relevant participants",
            "observable_indicators": [
                "Each cited item can be traced to its source.",
                "Any correction or unresolved disagreement is recorded.",
            ],
        },
        "limits": ["This candidate is a test fixture, not a substantive assessment."],
    }


class CLSSReasoningAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
        cls.by_id = {case["id"]: case for case in cls.cases if "expected_finding_type" in case}

    def validate_case(self, case, candidate):
        allowed = {
            item["evidence_id"] for item in case.get("evidence", [])
        }
        return validate_reasoning_candidate(candidate, case, input_evidence_ids=allowed)

    def test_expected_finding_types_are_checked_for_every_reasoning_fixture(self):
        for case in self.by_id.values():
            with self.subTest(case=case["id"]):
                result = self.validate_case(case, candidate_for(case))
                self.assertEqual(result["actual_finding_type"], case["expected_finding_type"])
                self.assertTrue(result["review_required"])
                self.assertTrue(result["human_review_criteria"])

    def test_wrong_finding_type_is_rejected(self):
        case = self.by_id["strong-supported-tension"]
        candidate = candidate_for(case, finding_type="insufficient_evidence")
        with self.assertRaisesRegex(ReasoningAcceptanceError, "finding mismatch"):
            self.validate_case(case, candidate)

    def test_missing_required_central_evidence_is_rejected(self):
        case = self.by_id["strong-supported-tension"]
        candidate = candidate_for(case, central_ids=["ev-commit"])
        with self.assertRaisesRegex(ReasoningAcceptanceError, "omits fixture-required evidence"):
            self.validate_case(case, candidate)

    def test_candidate_cannot_cite_evidence_not_in_the_case(self):
        case = self.by_id["no-defensible-tension"]
        candidate = candidate_for(case, central_ids=["ev-ghost"])
        with self.assertRaisesRegex(ReasoningAcceptanceError, "unknown evidence"):
            self.validate_case(case, candidate)


if __name__ == "__main__":
    unittest.main()
