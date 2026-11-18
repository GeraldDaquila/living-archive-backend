"""Source-independent Gold Star v2.0 response-floor gate.

This is a conservative release boundary, not a semantic grader. It enforces
machine-verifiable minimums for every visitor answer while leaving question-fit,
epistemic quality, and substantive adequacy to the route-specific acceptance
contracts and human-reviewed benchmarks. Frozen exact answers are never edited.

Gold Star v3 semantic checks run in SHADOW mode inside this existing boundary.
Their result is reported separately and can never alter the v2 decision, answer,
HTTP status, recommendation, or visitor-visible composition.
"""
from __future__ import annotations

import re
from typing import Any, Dict

VERSION = "2.0"
SEMANTIC_SHADOW_VERSION = "1.0"
ANSWER_KEYS = ("response", "answer")
NON_ANSWER_MARKERS = (
    "i cannot answer that question",
    "i can't answer that question",
    "i am unable to answer",
    "i'm unable to answer",
    "the guide could not complete this question",
    "please rephrase your question",
)


def _semantic_shadow(query: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Observe semantic task fit without enforcing, rewriting, or blocking."""
    try:
        from gold_star_semantic_contract import evaluate_semantic_contract
        result = evaluate_semantic_contract(query, payload)
        return {
            "version": SEMANTIC_SHADOW_VERSION,
            "mode": "shadow_only",
            "status": result.get("status", "review_required"),
            "reason": result.get("reason", "unspecified"),
            "question_type": result.get("question_type", "unknown"),
            "checks": result.get("checks", []),
            "failed_checks": result.get("failed_checks", []),
            "hard_failures": result.get("hard_failures", []),
            "review_flags": result.get("review_flags", []),
            "semantic_certification": False,
            "enforced": False,
        }
    except Exception as exc:
        # Shadow diagnostics must never affect visitor availability.
        return {
            "version": SEMANTIC_SHADOW_VERSION,
            "mode": "shadow_only",
            "status": "observer_error",
            "reason": type(exc).__name__,
            "semantic_certification": False,
            "enforced": False,
        }


def evaluate_response_floor(query: str, payload: Any, *, exact_standard: bool = False) -> Dict[str, Any]:
    """Return the integrity gate decision plus a non-enforcing semantic observation."""
    if not isinstance(payload, dict):
        return {"version": VERSION, "status": "not_applicable", "reason": "non_object_payload"}
    if payload.get("ok") is False:
        return {"version": VERSION, "status": "not_applicable", "reason": "explicit_error_payload"}
    if payload.get("handoff_pending") is True or (
        payload.get("handoff") and not any(str(payload.get(key) or "").strip() for key in ANSWER_KEYS)
    ):
        return {"version": VERSION, "status": "not_applicable", "reason": "structured_handoff"}

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

    result = {
        "version": VERSION,
        "status": "pass",
        "reason": "minimum_response_integrity_satisfied",
        "source_independent": True,
        "exact_standard_immutable": bool(exact_standard),
    }
    # Shadow diagnostics are metadata only. A semantic hard failure is not
    # promoted into the v2 enforcement status and cannot change the answer.
    result["semantic_shadow"] = _semantic_shadow(query, payload)
    return result
