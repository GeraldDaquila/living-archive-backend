"""Session-local normalization for CLSS questionnaire answers.

This module preserves visitor text and explicit provenance. It does not infer
source types, motives, findings, or consequences and performs no network or
persistence operations.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

PROMPT_DIMENSIONS = {
    "responsibility-service": "commitment",
    "concrete-episode": "conduct",
    "consequences": "consequences",
    "commitment-conduct-comparison": "coherence",
    "accountability": "accountability",
    "counterevidence-context": "counterevidence",
    "correction-change": "correction",
    "most-consequential-unknown": "unknown",
}
ALLOWED_MODES = {"self", "third_party"}
ALLOWED_SOURCES = {
    "self_report",
    "first_hand_observation",
    "documented_outcome",
    "second_hand_report",
    "interpretation",
    "unknown",
}
OPTIONAL_CONTEXT_FIELDS = (
    "context",
    "affected_parties",
    "observations",
    "reported_effects",
    "visitor_interpretation",
    "counterevidence",
    "uncertainties",
)


class CLSSNormalizationError(ValueError):
    """Raised when a questionnaire payload violates the input contract."""


def normalize_questionnaire_answers(
    answers: Sequence[Mapping[str, Any]],
    *,
    mode: str,
) -> dict[str, Any]:
    """Return normalized evidence and missing dimensions without adverse inference."""
    if mode not in ALLOWED_MODES:
        raise CLSSNormalizationError("mode must be self or third_party")
    if not isinstance(answers, Sequence) or isinstance(answers, (str, bytes)):
        raise CLSSNormalizationError("answers must be a sequence of answer objects")

    evidence = []
    answered_dimensions = set()
    seen_prompts = set()
    missing_dimensions = []
    for answer in answers:
        if not isinstance(answer, Mapping):
            raise CLSSNormalizationError("each answer must be an object")
        prompt_id = answer.get("prompt_id")
        if prompt_id not in PROMPT_DIMENSIONS:
            raise CLSSNormalizationError(f"unknown prompt_id: {prompt_id!r}")
        if prompt_id in seen_prompts:
            raise CLSSNormalizationError(f"duplicate prompt_id: {prompt_id!r}")
        seen_prompts.add(prompt_id)
        dimension = PROMPT_DIMENSIONS[prompt_id]
        text = answer.get("answer_text")
        if text is None or (isinstance(text, str) and not text.strip()):
            missing_dimensions.append(dimension)
            continue
        if not isinstance(text, str):
            raise CLSSNormalizationError("answer_text must be text")
        source_type = answer.get("source_type", "unknown")
        if source_type not in ALLOWED_SOURCES:
            raise CLSSNormalizationError(f"invalid source_type: {source_type!r}")

        evidence_id = f"clss-{prompt_id}"
        item = {
            "evidence_id": evidence_id,
            "prompt_id": prompt_id,
            "dimension": dimension,
            "answer_text": text,
            "source_type": source_type,
            "provenance": {
                "mode": mode,
                "source_type_was_explicit": "source_type" in answer,
                "source_prompt_ids": [prompt_id],
            },
        }
        for field in OPTIONAL_CONTEXT_FIELDS:
            if field in answer:
                value = answer[field]
                if not isinstance(value, (str, list, tuple)):
                    raise CLSSNormalizationError(f"{field} must be text or a list of text")
                if isinstance(value, (list, tuple)) and not all(isinstance(v, str) for v in value):
                    raise CLSSNormalizationError(f"{field} list must contain only text")
                item[field] = list(value) if isinstance(value, (list, tuple)) else [value]
        evidence.append(item)
        answered_dimensions.add(dimension)

    # Any questionnaire prompt not supplied at all is also missing; absence is
    # recorded as a gap, never as negative evidence about the respondent.
    for prompt_id, dimension in PROMPT_DIMENSIONS.items():
        if prompt_id not in seen_prompts:
            missing_dimensions.append(dimension)
    missing_dimensions = list(dict.fromkeys(missing_dimensions))
    return {
        "mode": mode,
        "evidence": evidence,
        "missing_dimensions": missing_dimensions,
        "normalization_notes": [
            "Original answer_text is preserved without rewriting.",
            "An omitted source_type is marked unknown; it is never guessed.",
            "Missing answers and dimensions are gaps, not adverse evidence.",
            "Third-party mode does not establish private intent or motive.",
        ],
    }
