"""Provider-independent structural/safety validator for CLSS candidate responses.

This module enforces machine-checkable contract rules only. It cannot determine
whether natural-language claims are semantically supported by cited evidence.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

ALLOWED_MODES = {"self", "third_party"}
ALLOWED_PATHS = {"llm", "deterministic_fallback"}
ALLOWED_FINDING_TYPES = {
    "supported_tension",
    "mixed_evidence",
    "insufficient_evidence",
    "no_defensible_tension",
}
FORBIDDEN_LANGUAGE = (
    re.compile(r"\bshould not be promoted\b", re.I),
    re.compile(r"\bnot suitable for (?:the )?role\b", re.I),
    re.compile(r"\bdiagnos(?:e|ed|is|tic)\b", re.I),
    re.compile(r"\b(?:score|rank(?:ed|ing)?)\s+(?:of|this person|the person|them|him|her)\b", re.I),
    re.compile(r"\b(?:is|was) manipulative\b", re.I),
)
REQUIRED_TOP_LEVEL = {
    "mode",
    "path",
    "central_incoherence",
    "why_it_matters",
    "what_the_evidence_says",
    "what_could_change_the_interpretation",
    "what_to_do_next",
    "limits",
}


class ResponseValidationError(ValueError):
    """Raised when a candidate response violates a structural safety invariant."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResponseValidationError(message)


def _nonempty_text(value: Any, label: str) -> None:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be non-empty text")


def _evidence_refs(value: Any, allowed_ids: set[str], label: str, *, required: bool) -> None:
    _require(isinstance(value, list), f"{label} must be a list")
    _require(all(isinstance(item, str) and item for item in value), f"{label} must contain non-empty string IDs")
    _require(len(value) == len(set(value)), f"{label} must not contain duplicate IDs")
    _require(set(value).issubset(allowed_ids), f"{label} references unknown evidence IDs")
    if required:
        _require(bool(value), f"{label} must cite at least one evidence ID")


def _check_text(text: str, label: str) -> None:
    for pattern in FORBIDDEN_LANGUAGE:
        _require(not pattern.search(text), f"{label} contains prohibited suitability, diagnostic, scoring, or motive language")


def validate_candidate_response(
    response: Mapping[str, Any],
    input_evidence_ids: set[str],
    *,
    mode: str,
    path: str,
) -> dict[str, Any]:
    """Validate structure and deterministic safety rules, returning a plain dict.

    Any failure raises ResponseValidationError; callers should reject the
    candidate and use the separately validated deterministic fallback.
    """
    _require(isinstance(response, Mapping), "response must be an object")
    _require(mode in ALLOWED_MODES, "input mode is invalid")
    _require(path in ALLOWED_PATHS, "response path is invalid")
    _require(set(response.keys()) == REQUIRED_TOP_LEVEL, "response fields do not match canonical contract")
    _require(response.get("mode") == mode, "response mode does not match input mode")
    _require(response.get("path") == path, "response path does not match the selected path")

    central = response.get("central_incoherence")
    _require(isinstance(central, Mapping), "central_incoherence must be an object")
    _require(set(central.keys()) == {"text", "finding_type", "evidence_ids"}, "central_incoherence fields are invalid")
    _nonempty_text(central.get("text"), "central_incoherence.text")
    _require(central.get("finding_type") in ALLOWED_FINDING_TYPES, "central finding type is invalid")
    _evidence_refs(
        central.get("evidence_ids"), input_evidence_ids, "central_incoherence.evidence_ids",
        required=central.get("finding_type") in {"supported_tension", "mixed_evidence"},
    )

    why = response.get("why_it_matters")
    _require(isinstance(why, Mapping) and set(why.keys()) == {"text", "evidence_ids"}, "why_it_matters shape is invalid")
    _nonempty_text(why.get("text"), "why_it_matters.text")
    _evidence_refs(why.get("evidence_ids"), input_evidence_ids, "why_it_matters.evidence_ids", required=False)

    for field in ("what_the_evidence_says", "what_could_change_the_interpretation"):
        entries = response.get(field)
        _require(isinstance(entries, list), f"{field} must be a list")
        for index, entry in enumerate(entries):
            label = f"{field}[{index}]"
            _require(isinstance(entry, Mapping) and set(entry.keys()) == {"text", "evidence_ids"}, f"{label} shape is invalid")
            _nonempty_text(entry.get("text"), f"{label}.text")
            _evidence_refs(entry.get("evidence_ids"), input_evidence_ids, f"{label}.evidence_ids", required=False)

    next_step = response.get("what_to_do_next")
    _require(isinstance(next_step, Mapping) and set(next_step.keys()) == {"action", "owner", "observable_indicators"}, "what_to_do_next shape is invalid")
    _nonempty_text(next_step.get("action"), "what_to_do_next.action")
    _require(next_step.get("owner") is None or isinstance(next_step.get("owner"), str), "next-step owner must be text or null")
    _require(isinstance(next_step.get("observable_indicators"), list), "observable_indicators must be a list")
    _require(bool(next_step["observable_indicators"]), "at least one observable indicator is required")
    for index, indicator in enumerate(next_step["observable_indicators"]):
        _nonempty_text(indicator, f"observable_indicators[{index}]")

    _require(isinstance(response.get("limits"), list), "limits must be a list")
    for index, limit in enumerate(response["limits"]):
        _nonempty_text(limit, f"limits[{index}]")

    # Gather all visitor-facing prose before applying whole-response safety rules.
    texts = [central["text"], why["text"]]
    texts.extend(item["text"] for item in response["what_the_evidence_says"])
    texts.extend(item["text"] for item in response["what_could_change_the_interpretation"])
    texts.append(next_step["action"])
    texts.extend(next_step["observable_indicators"])
    texts.extend(response["limits"])

    # Third-party mode may describe observed actions, but cannot assert private intent.
    if mode == "third_party":
        private_intent = re.compile(
            r"\b(?:secretly wants|intends to|doesn't care about|does not care about|is unwilling to serve)\b",
            re.I,
        )
        for index, text in enumerate(texts):
            _require(
                not private_intent.search(text),
                f"visitor-facing text[{index}] asserts third-party private intent",
            )

    # Structural validation is not a substitute for semantic entailment checking.
    for index, text in enumerate(texts):
        _check_text(text, f"visitor-facing text[{index}]")

    return dict(response)


def validate_or_fallback(
    candidate_response: Any,
    fallback_response: Mapping[str, Any],
    input_evidence_ids: set[str],
    *,
    mode: str,
) -> tuple[dict[str, Any], str]:
    """Validate an LLM candidate; reject it and validate fallback on any failure.

    Returns (validated_response, selected_path). If fallback validation also
    fails, the exception is propagated so callers can fail closed rather than
    display an unvalidated response.
    """
    try:
        accepted = validate_candidate_response(
            candidate_response, input_evidence_ids, mode=mode, path="llm"
        )
        return accepted, "llm"
    except (ResponseValidationError, TypeError, KeyError, AttributeError):
        accepted_fallback = validate_candidate_response(
            fallback_response, input_evidence_ids, mode=mode, path="deterministic_fallback"
        )
        return accepted_fallback, "deterministic_fallback"

