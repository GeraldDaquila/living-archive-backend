"""Fixture-driven acceptance checks for CLSS contextual reasoning candidates.

This module is an integration gate, not a reasoning engine. A future provider or
production adapter can submit a candidate response against a design fixture.
Acceptance requires both the canonical response contract and the fixture's
expected finding type / evidence coverage. Passing these tests does not itself
prove a model's semantic interpretation is correct; the fixture set remains the
human-authored reference.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tests.clss_response_validator import (
    ResponseValidationError,
    validate_candidate_response,
)


class ReasoningAcceptanceError(ValueError):
    """Raised when a candidate fails fixture-specific acceptance criteria."""


def validate_reasoning_candidate(
    candidate: Mapping[str, Any],
    fixture: Mapping[str, Any],
    *,
    input_evidence_ids: set[str],
) -> dict[str, Any]:
    """Validate response shape/safety and fixture-specific finding/evidence rules."""
    mode = fixture.get("mode")
    expected = fixture.get("expected_finding_type")
    if not isinstance(expected, str):
        raise ReasoningAcceptanceError("fixture has no expected_finding_type")

    try:
        validated = validate_candidate_response(
            candidate,
            input_evidence_ids,
            mode=mode,
            path="llm",
        )
    except (ResponseValidationError, TypeError, ValueError) as exc:
        raise ReasoningAcceptanceError(f"candidate violates response contract: {exc}") from exc

    actual = validated["central_incoherence"]["finding_type"]
    if actual != expected:
        raise ReasoningAcceptanceError(
            f"finding mismatch for {fixture.get('id')}: expected {expected}, got {actual}"
        )

    required_ids = set(fixture.get("must_include_evidence_ids", []))
    cited_ids = set(validated["central_incoherence"]["evidence_ids"])
    if not required_ids.issubset(cited_ids):
        missing = sorted(required_ids - cited_ids)
        raise ReasoningAcceptanceError(
            f"central finding omits fixture-required evidence IDs: {missing}"
        )

    all_text = [validated["central_incoherence"]["text"]]
    all_text.extend(item["text"] for item in validated["what_the_evidence_says"])
    all_text.extend(item["text"] for item in validated["what_could_change_the_interpretation"])
    preserve_rules = fixture.get("must_preserve", [])
    # These requirements are intentionally surfaced to a reviewer rather than
    # treated as machine-proven semantic facts. A string match cannot establish
    # whether a nuanced claim is adequately preserved.
    return {
        "response": validated,
        "expected_finding_type": expected,
        "actual_finding_type": actual,
        "required_evidence_ids": sorted(required_ids),
        "cited_evidence_ids": sorted(cited_ids),
        "review_required": True,
        "human_review_criteria": list(preserve_rules),
        "candidate_text_for_review": all_text,
        "note": "Automated checks cover contract, finding label, and evidence coverage only; human review is still required for semantic fidelity.",
    }
