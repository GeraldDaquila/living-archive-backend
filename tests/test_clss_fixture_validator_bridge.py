"""Bridge all CLSS design fixtures through the canonical response validator.

These tests verify response-contract compatibility and evidence-ID integrity only.
They do not score semantic reasoning or claim production behavior is implemented.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.clss_response_validator import (
    ResponseValidationError,
    validate_candidate_response,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "clss" / "stewardship-coherence-cases.json"
)


def _response_for_fixture(case, evidence_ids):
    """Build a neutral contract-shaped response, not a substantive reasoning result."""
    finding_type = case["expected_finding_type"]
    citations = list(case.get("must_include_evidence_ids", []))
    if not citations:
        citations = list(evidence_ids)[:1]

    return {
        "mode": case["mode"],
        "path": "deterministic_fallback",
        "central_incoherence": {
            "text": "Contract test placeholder: finding text must be produced by the actual reasoning implementation.",
            "finding_type": finding_type,
            "evidence_ids": citations,
        },
        "why_it_matters": {
            "text": "Contract test placeholder: impact must be grounded in the actual evidence.",
            "evidence_ids": list(evidence_ids)[:1],
        },
        "what_the_evidence_says": [
            {
                "text": "Contract test placeholder: evidence interpretation must preserve source provenance.",
                "evidence_ids": list(evidence_ids)[:1],
            }
        ],
        "what_could_change_the_interpretation": [
            {
                "text": "Contract test placeholder: identify a material unknown or counterexample from the case.",
                "evidence_ids": list(evidence_ids)[:1],
            }
        ],
        "what_to_do_next": {
            "action": "Contract test placeholder: actual implementation must produce a case-specific next step.",
            "owner": None,
            "observable_indicators": [
                "Contract test placeholder: actual implementation must define an observable indicator."
            ],
        },
        "limits": ["This is a schema bridge test, not a visitor-facing response."],
    }


class FixtureValidatorBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.cases = cls.document["cases"]

    def test_every_reasoning_fixture_finding_type_passes_contract_shape(self):
        for case in self.cases:
            if "expected_finding_type" not in case:
                continue
            with self.subTest(case=case["id"]):
                evidence_ids = {
                    item["evidence_id"] for item in case.get("evidence", [])
                }
                evidence_ids.update(case.get("input_evidence_ids", []))
                response = _response_for_fixture(case, evidence_ids)
                validate_candidate_response(
                    response,
                    evidence_ids,
                    mode=case["mode"],
                    path="deterministic_fallback",
                )

    def test_fixture_required_evidence_is_present_in_central_finding(self):
        for case in self.cases:
            if "expected_finding_type" not in case:
                continue
            with self.subTest(case=case["id"]):
                evidence_ids = {
                    item["evidence_id"] for item in case.get("evidence", [])
                }
                evidence_ids.update(case.get("input_evidence_ids", []))
                response = _response_for_fixture(case, evidence_ids)
                self.assertTrue(
                    set(case.get("must_include_evidence_ids", [])).issubset(
                        set(response["central_incoherence"]["evidence_ids"])
                    )
                )

    def test_invalid_llm_fixture_reference_is_rejected_by_validator(self):
        case = next(
            item for item in self.cases
            if item["id"] == "llm-invalid-output-fallback"
        )
        evidence_ids = set(case["input_evidence_ids"])
        base_case = next(
            item for item in self.cases
            if item.get("expected_finding_type") == "supported_tension"
        )
        response = _response_for_fixture(base_case, evidence_ids)
        response["mode"] = case["mode"]
        response["central_incoherence"]["evidence_ids"] = (
            case["invalid_llm_output"]["central_incoherence"]["evidence_ids"]
        )
        with self.assertRaisesRegex(ResponseValidationError, "unknown evidence"):
            validate_candidate_response(
                response, evidence_ids, mode=case["mode"], path="deterministic_fallback"
            )


if __name__ == "__main__":
    unittest.main()
