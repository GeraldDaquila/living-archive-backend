"""Source-independent Gold Star v2.0 response-floor gate.

This is a conservative release boundary, not a universal semantic grader. It
enforces machine-verifiable minimums for every visitor answer and promotes only
explicitly supported, task-specific semantic contracts into bounded enforcement.
Unknown task types remain review-required. Frozen exact answers are never edited.

Semantic observations remain non-certifying. For supported task families, hard
contract violations can fail the shared answer floor; they never rewrite answer
text, choose a doorway, or claim semantic certification.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from gold_star_question_contract import build_question_contract, validate_question_contract
from gold_star_answer_envelope import build_answer_envelope, validate_answer_envelope
from gold_star_evidence_validation import validate_evidence_payload
from institutional_learning_failure_contract import is_institutional_learning_failure_question
from social_mechanism_grounding_contract import (
    requires_grounded_mechanism_example,
    has_grounded_mechanism_example,
)

VERSION = "2.2"
SEMANTIC_SHADOW_VERSION = "1.1"
SEMANTIC_ENFORCED_QUESTION_TYPES = frozenset({"institutional_learning_failure", "conceptual_relationship", "comparison", "lived_reflective_inquiry", "epistemic_distress", "epistemic_distress_guidance"})
ANSWER_KEYS = ("response", "answer")
NON_ANSWER_MARKERS = (
    "i cannot answer that question",
    "i can't answer that question",
    "i am unable to answer",
    "i'm unable to answer",
    "the guide could not complete this question",
    "i couldn't produce a reliable answer to that question just now",
    "i couldn’t produce a reliable answer to that question just now",
    "i could not produce a reliable answer to that question just now",
    "please rephrase your question",
)


def _semantic_shadow(query: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Observe semantic task fit; supported bounded families are enforced by the v2 gate."""
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
    intent = str(payload.get("intent") or "").strip().upper()
    route_source = str(payload.get("origin_route_source") or payload.get("route_source") or "").strip()
    if intent in {"SAFETY_INTERRUPT", "SAFETY_CONVERSATION"} or route_source == "bounded_safety_conversation":
        question_contract = build_question_contract(query)
        answer_envelope = build_answer_envelope(
            query, payload, question_contract, exact_standard=exact_standard
        )
        envelope_validation = validate_answer_envelope(answer_envelope)
        if not envelope_validation.get("valid"):
            return {"version": VERSION, "status": "fail", "reason": "safety_envelope_invalid"}
        return {
            "version": VERSION,
            "status": "not_applicable",
            "reason": "safety_intervention_route",
            "source_independent": True,
            "exact_standard_immutable": bool(exact_standard),
            "question_contract": question_contract,
            "question_contract_validation": validate_question_contract(question_contract),
            "answer_envelope": answer_envelope,
            "answer_envelope_validation": envelope_validation,
            "semantic_shadow": {
                "version": SEMANTIC_SHADOW_VERSION,
                "mode": "not_applicable",
                "status": "safety_intervention_exempt",
                "semantic_certification": False,
                "enforced": False,
            },
        }
    if payload.get("handoff_pending") is True or (
        payload.get("handoff") and not any(str(payload.get(key) or "").strip() for key in ANSWER_KEYS)
    ):
        return {"version": VERSION, "status": "not_applicable", "reason": "structured_handoff"}

    question_contract = build_question_contract(query)
    contract_validation = validate_question_contract(question_contract)
    if not contract_validation.get("valid"):
        return {"version": VERSION, "status": "fail", "reason": "question_contract_invalid"}

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
    # This contract is enforced at the outer visitor response floor as well as
    # inside provider parsing. It therefore covers deterministic recovery,
    # cache reuse, compatibility paths, and late response transformations.
    # Exact approved answers remain immutable and are evaluated by their own
    # registry contract.
    if (
        not exact_standard
        and requires_grounded_mechanism_example(query)
        and not has_grounded_mechanism_example(answer)
    ):
        return {
            "version": VERSION,
            "status": "fail",
            "reason": "social_mechanism_example_not_demonstrated",
            "social_mechanism_grounding": {
                "version": "1.0",
                "required": True,
                "demonstrated": False,
            },
        }

    answer_envelope = build_answer_envelope(
        query, payload, question_contract, exact_standard=exact_standard
    )
    envelope_validation = validate_answer_envelope(answer_envelope)
    if not envelope_validation.get("valid"):
        return {"version": VERSION, "status": "fail", "reason": "answer_envelope_invalid"}

    evidence_validation = validate_evidence_payload(
        query, payload, exact_standard=exact_standard
    )
    if evidence_validation.get("status") == "fail":
        return {
            "version": VERSION,
            "status": "fail",
            "reason": evidence_validation.get("reason") or "evidence_validation_failed",
            "question_contract": question_contract,
            "question_contract_validation": contract_validation,
            "answer_envelope": answer_envelope,
            "answer_envelope_validation": envelope_validation,
            "evidence_validation": evidence_validation,
            "semantic_certification": False,
        }

    result = {
        "version": VERSION,
        "status": "pass",
        "reason": "minimum_response_integrity_satisfied",
        "source_independent": True,
        "exact_standard_immutable": bool(exact_standard),
        "question_contract": question_contract,
        "question_contract_validation": contract_validation,
        "answer_envelope": answer_envelope,
        "answer_envelope_validation": envelope_validation,
        "evidence_validation": evidence_validation,
        "bounded_repair": payload.get("bounded_repair") or {
            "status": "not_attempted", "attempts": 0, "max_attempts": 1
        },
        "personal_reference_resolution": question_contract.get("personal_reference"),
    }
    # Semantic observations remain non-enforcing by default. Only the explicitly
    # supported question families below can contribute bounded v2 requirements.
    result["semantic_shadow"] = _semantic_shadow(query, payload)
    semantic = result["semantic_shadow"]
    supported_semantic_type = (
        semantic.get("question_type") in SEMANTIC_ENFORCED_QUESTION_TYPES
        or is_institutional_learning_failure_question(query)
    )
    if not exact_standard and supported_semantic_type:
        # A failed or unavailable semantic observer cannot silently downgrade
        # an explicitly supported task family back to the generic integrity-only floor.
        semantic_failed = (
            semantic.get("status") != "review_required"
            or semantic.get("question_type") not in SEMANTIC_ENFORCED_QUESTION_TYPES
        )
        result["semantic_enforcement"] = {
            "version": "1.0",
            "mode": "bounded_supported_contract",
            "status": "fail" if semantic_failed else "pass",
            "enforced": True,
            "question_type": semantic.get("question_type"),
            "failed_checks": semantic.get("failed_checks") or [],
            "reason": (
                "supported_semantic_contract_failed"
                if semantic_failed else "supported_semantic_contract_satisfied"
            ),
        }
        if semantic_failed:
            result["status"] = "fail"
            result["reason"] = "supported_semantic_contract_failed"
    else:
        result["semantic_enforcement"] = {
            "version": "1.0",
            "mode": "bounded_supported_contract",
            "status": "not_applicable",
            "enforced": False,
            "reason": (
                "exact_gold_standard_immutable"
                if exact_standard else "no_enforced_supported_question_type"
            ),
        }
    # Gold Star v3 makes the three semantic operating states explicit.
    # This is reporting-only: it does not change the v2 pass/fail decision.
    enforcement = result.get("semantic_enforcement") or {}
    observation = result.get("semantic_shadow") or {}
    result["semantic_governance"] = {
        "version": "3.0",
        "diagnostic_observation": {
            "state": "available" if observation.get("status") != "observer_error" else "unavailable",
            "mode": observation.get("mode", "unknown"),
            "status": observation.get("status", "unknown"),
            "question_type": observation.get("question_type", "unknown"),
        },
        "bounded_enforcement": {
            "state": "active" if enforcement.get("enforced") is True else "inactive",
            "status": enforcement.get("status", "not_applicable"),
            "question_type": enforcement.get("question_type"),
        },
        "semantic_certification": {
            "state": "not_certified",
            "certified": False,
            "reason": "heuristic_contracts_and_offline_calibration_do_not_establish_semantic_certification",
        },
    }
    return result


def apply_response_floor_boundary(
    query: str,
    payload: Any,
    status_code: int = 200,
    *,
    exact_standard: bool = False,
) -> tuple[Any, int]:
    """Apply the same fail-closed v2 integrity gate at every JSON boundary."""
    if not isinstance(payload, dict):
        return payload, int(status_code)
    try:
        floor_result = evaluate_response_floor(
            query, payload, exact_standard=exact_standard
        )
    except Exception as exc:
        floor_result = {
            "version": VERSION,
            "status": "fail",
            "reason": "quality_gate_unavailable",
            "failure_type": type(exc).__name__,
        }
    safe_payload = dict(payload)
    safe_payload["gold_star_v2_quality_floor"] = floor_result
    final_status = int(status_code)
    recovery = safe_payload.get("visitor_transport_recovery")
    if (
        floor_result.get("status") == "pass"
        and safe_payload.get("ok") is True
        and isinstance(recovery, dict)
        and recovery.get("status") == "recovered"
        and recovery.get("answer_recovered") is True
        and final_status >= 400
    ):
        # Restore success only after the substantive answer and v2 floor pass.
        final_status = 200
        recovery = dict(recovery)
        recovery["http_status_restored"] = True
        safe_payload["visitor_transport_recovery"] = recovery
    if floor_result.get("status") == "fail" and 200 <= final_status < 300:
        safe_payload = {
            "ok": False,
            "version": safe_payload.get("version"),
            "query": str(query or ""),
            "error_type": "gold_star_v2_quality_floor_rejected",
            "failure_kind": "application_contract",
            "retryable": False,
            "visitor_acceptance_contract": "v1",
            "response": "",
            "gold_star_v2_quality_floor": floor_result,
            "message": "The response did not pass the minimum integrity checks. Please try again.",
        }
        final_status = 503
    return safe_payload, final_status
