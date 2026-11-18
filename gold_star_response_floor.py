"""Source-independent Gold Star v2.0 response-floor gate.

This is a conservative release boundary, not a semantic grader. It enforces
machine-verifiable minimums for every visitor answer while leaving question-fit,
epistemic quality, and substantive adequacy to the route-specific acceptance
contracts and human-reviewed benchmarks. Frozen exact answers are never edited.
"""
from __future__ import annotations

import re
from typing import Any, Dict

VERSION = "2.0"
ANSWER_KEYS = ("response", "answer")
NON_ANSWER_MARKERS = (
    "i cannot answer that question",
    "i can't answer that question",
    "i am unable to answer",
    "i'm unable to answer",
    "the guide could not complete this question",
    "please rephrase your question",
)


def evaluate_response_floor(query: str, payload: Any, *, exact_standard: bool = False) -> Dict[str, Any]:
    """Return a deterministic audit decision without rewriting response content."""
    if not isinstance(payload, dict):
        return {"version": VERSION, "status": "not_applicable", "reason": "non_object_payload"}
    if payload.get("ok") is False:
        return {"version": VERSION, "status": "not_applicable", "reason": "explicit_error_payload"}

    answer = next((str(payload.get(key) or "").strip() for key in ANSWER_KEYS
                   if str(payload.get(key) or "").strip()), "")
    if not answer:
        return {"version": VERSION, "status": "fail", "reason": "missing_answer"}
    if len(answer) > 30000:
        return {"version": VERSION, "status": "fail", "reason": "answer_exceeds_contract_limit"}
    if re.search(r"<\s*(?:script|style|html|body|iframe)\b", answer, re.I):
        return {"version": VERSION, "status": "fail", "reason": "unsafe_markup"}
    folded = re.sub(r"\s+", " ", answer.casefold()).strip()
    if any(marker in folded for marker in NON_ANSWER_MARKERS):
        return {"version": VERSION, "status": "fail", "reason": "generic_nonanswer"}
    if not str(query or "").strip():
        return {"version": VERSION, "status": "fail", "reason": "missing_query_context"}
    return {
        "version": VERSION,
        "status": "pass",
        "reason": "minimum_response_integrity_satisfied",
        "source_independent": True,
        "exact_standard_immutable": bool(exact_standard),
    }
