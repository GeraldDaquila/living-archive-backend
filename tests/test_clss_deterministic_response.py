"""Tests for the validated, conservative CLSS canonical fallback composer."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.clss_deterministic_response import build_deterministic_response
from tests.clss_response_validator import validate_candidate_response, validate_or_fallback

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "clss" / "stewardship-coherence-cases.json"
)


class CLSSDeterministicResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]

    def test_all_evidence_fixtures_produce_valid_canonical_fallback(self):
        for case in self.cases:
            if not case.get("evidence"):
                continue
            with self.subTest(case=case["id"]):
                response = build_deterministic_response(
                    case["evidence"],
                    mode=case["mode"],
                    missing_dimensions=case.get("missing_dimensions", []),
                )
                input_ids = {item["evidence_id"] for item in case["evidence"]}
                validate_candidate_response(
                    response,
                    input_ids,
                    mode=case["mode"],
                    path="deterministic_fallback",
                )
                self.assertEqual(response["path"], "deterministic_fallback")
                self.assertTrue(response["central_incoherence"]["evidence_ids"])
                self.assertEqual(
                    response["central_incoherence"]["finding_type"],
                    "mixed_evidence"
                    if case["id"] in {
                        "mixed-evidence-with-repair",
                        "conflicting-source-provenance",
                    }
                    else "insufficient_evidence",
                )

    def test_evidence_provenance_is_preserved_in_visitor_response(self):
        case = next(c for c in self.cases if c["id"] == "conflicting-source-provenance")
        response = build_deterministic_response(case["evidence"], mode=case["mode"])
        rendered = " ".join(item["text"] for item in response["what_the_evidence_says"])
        self.assertIn("firsthand observation", rendered)
        self.assertIn("secondhand report", rendered)
        self.assertIn("ev-direct", rendered)
        self.assertIn("ev-rumor", rendered)

    def test_missing_dimensions_are_explicitly_non_adverse(self):
        case = next(c for c in self.cases if c["id"] == "missing-answer-is-not-adverse")
        response = build_deterministic_response(
            case["evidence"],
            mode=case["mode"],
            missing_dimensions=case["missing_dimensions"],
        )
        text = " ".join(
            item["text"] for item in response["what_could_change_the_interpretation"]
        )
        self.assertIn("not adverse evidence", text)
        self.assertIn("consequences", text)
        self.assertIn("accountability", text)

    def test_invalid_llm_candidate_is_rejected_and_real_fallback_is_validated(self):
        invalid_case = next(
            c for c in self.cases if c["id"] == "llm-invalid-output-fallback"
        )
        evidence_case = next(
            c for c in self.cases if c["id"] == "insufficient-evidence-labels-only"
        )
        evidence = evidence_case["evidence"]
        evidence_ids = {item["evidence_id"] for item in evidence}
        fallback = build_deterministic_response(evidence, mode="third_party")
        invalid_candidate = {
            "mode": "third_party",
            "path": "llm",
            "central_incoherence": {
                "text": invalid_case["invalid_llm_output"]["central_incoherence"]["text"],
                "finding_type": "supported_tension",
                "evidence_ids": invalid_case["invalid_llm_output"]["central_incoherence"]["evidence_ids"],
            },
            "why_it_matters": {"text": "Unsupported conclusion.", "evidence_ids": []},
            "what_the_evidence_says": [],
            "what_could_change_the_interpretation": [],
            "what_to_do_next": {
                "action": "Make a decision.",
                "owner": None,
                "observable_indicators": ["Decision made."],
            },
            "limits": [],
        }
        accepted, selected_path = validate_or_fallback(
            invalid_candidate, fallback, evidence_ids, mode="third_party"
        )
        self.assertEqual(selected_path, "deterministic_fallback")
        self.assertEqual(accepted["path"], "deterministic_fallback")
        self.assertEqual(
            accepted["central_incoherence"]["finding_type"], "insufficient_evidence"
        )
        validate_candidate_response(
            accepted,
            evidence_ids,
            mode="third_party",
            path="deterministic_fallback",
        )

    def test_empty_evidence_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "without at least one evidence item"):
            build_deterministic_response([], mode="third_party")

    def test_response_is_not_claimed_to_be_a_final_coherence_finding(self):
        case = next(c for c in self.cases if c["id"] == "strong-supported-tension")
        response = build_deterministic_response(case["evidence"], mode=case["mode"])
        self.assertEqual(
            response["central_incoherence"]["finding_type"], "insufficient_evidence"
        )
        self.assertIn(
            "does not establish a defensible conclusion",
            response["central_incoherence"]["text"],
        )


if __name__ == "__main__":
    unittest.main()
