"""Eligibility gate for one bounded, evidence-directed composition repair."""
from __future__ import annotations

import re
from typing import Any, Dict

from gold_star_route_capabilities import route_capability
from guide_request_budget import can_attempt_repair

VERSION = "1.0"
MAX_REPAIR_ATTEMPTS = 1
REPAIRABLE_FAILURES = frozenset({
    "missing_answer",
    "generic_nonanswer",
    "answer_exceeds_contract_limit",
    "unsafe_markup",
    "supported_semantic_contract_failed",
})


def repair_eligibility(
    floor_result: Any,
    route_source: str,
    reasoning_mode: str,
    composition_available: bool,
    already_attempted: bool,
    deadline_monotonic: float | None,
    *,
    exact_standard: bool = False,
    now: float | None = None,
) -> Dict[str, Any]:
    """Allow one repair only for observable composition defects and a capable route."""
    if not isinstance(floor_result, dict) or floor_result.get("status") != "fail":
        return {"version": VERSION, "eligible": False, "reason": "no_enforceable_defect", "max_attempts": MAX_REPAIR_ATTEMPTS}
    failure = str(floor_result.get("reason") or "")
    failed_checks: list[str] = []
    if failure == "supported_semantic_contract_failed":
        semantic = floor_result.get("semantic_enforcement")
        raw_checks = semantic.get("failed_checks") if isinstance(semantic, dict) else None
        if isinstance(raw_checks, list):
            failed_checks = [
                value for value in raw_checks
                if isinstance(value, str) and re.fullmatch(r"[a-z0-9_]{1,64}", value)
            ][:8]
        if not failed_checks:
            return {
                "version": VERSION, "eligible": False,
                "reason": "semantic_failure_codes_unavailable",
                "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS,
            }
    if failure not in REPAIRABLE_FAILURES:
        return {"version": VERSION, "eligible": False, "reason": "defect_not_safely_repairable", "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS}
    if exact_standard:
        return {"version": VERSION, "eligible": False, "reason": "exact_standard_immutable", "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS}
    capability = route_capability(route_source)
    if capability.get("route_class") != "guide_composition":
        return {"version": VERSION, "eligible": False, "reason": "route_not_composition_capable", "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS}
    if str(reasoning_mode or "").strip().casefold() == "deterministic_only":
        return {"version": VERSION, "eligible": False, "reason": "deterministic_only_mode", "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS}
    if not composition_available:
        return {"version": VERSION, "eligible": False, "reason": "composition_result_unavailable", "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS}
    if already_attempted:
        return {"version": VERSION, "eligible": False, "reason": "repair_already_attempted", "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS}
    if deadline_monotonic is None or not can_attempt_repair(
        float(deadline_monotonic), already_attempted=False, now=now
    ):
        return {"version": VERSION, "eligible": False, "reason": "request_budget_reserve_unavailable", "failed_criterion": failure, "max_attempts": MAX_REPAIR_ATTEMPTS}
    return {
        "version": VERSION,
        "eligible": True,
        "reason": "single_bounded_composition_repair_available",
        "failed_criterion": failure,
        "failed_checks": failed_checks,
        "max_attempts": MAX_REPAIR_ATTEMPTS,
        "semantic_certification": False,
    }


def run_bounded_repair(
    payload: Dict[str, Any],
    decision: Dict[str, Any],
    *,
    compose_once,
    sanitize_response,
    validate_candidate,
    is_cross_question_leak,
    contains_unsafe_markup,
    fallback_provider: str = "",
    fallback_model: str = "",
):
    """Run exactly one composition repair and accept it only after full revalidation."""
    original = dict(payload) if isinstance(payload, dict) else {}
    failed_criterion = str((decision or {}).get("failed_criterion") or "")
    if not isinstance(decision, dict) or not decision.get("eligible"):
        outcome = {
            "status": "not_attempted",
            "attempts": 0,
            "max_attempts": MAX_REPAIR_ATTEMPTS,
            "reason": str((decision or {}).get("reason") or "repair_not_eligible"),
            "failed_criterion": failed_criterion or None,
        }
        original["bounded_repair"] = outcome
        return original, outcome

    try:
        candidate_result = compose_once()
    except Exception as exc:
        outcome = {
            "status": "failed",
            "attempts": 1,
            "max_attempts": MAX_REPAIR_ATTEMPTS,
            "reason": "composer_exception",
            "failure_type": type(exc).__name__,
            "failed_criterion": failed_criterion or None,
        }
        original["bounded_repair"] = outcome
        return original, outcome

    candidate_result = candidate_result if isinstance(candidate_result, dict) else {}
    try:
        candidate_response = str(
            sanitize_response(candidate_result.get("response") or candidate_result.get("answer") or "") or ""
        ).strip()
        invalid_candidate = (
            not candidate_response
            or bool(is_cross_question_leak(candidate_response))
            or bool(contains_unsafe_markup(candidate_response))
        )
        if invalid_candidate:
            outcome = {
                "status": "failed",
                "attempts": 1,
                "max_attempts": MAX_REPAIR_ATTEMPTS,
                "reason": "empty_cross_question_or_unsafe_repair",
                "failed_criterion": failed_criterion or None,
            }
            original["bounded_repair"] = outcome
            return original, outcome

        candidate_payload = dict(original)
        candidate_payload["response"] = candidate_response
        candidate_payload["response_provenance"] = {
            "class": "bounded_composition_repair",
            "provider": str(candidate_result.get("provider") or fallback_provider or "") or None,
            "model": str(candidate_result.get("model") or fallback_model or "") or None,
            "quality_adjusted_llm_eligible": True,
            "llm_invoked": True,
        }
        validation = validate_candidate(candidate_payload)
        if not isinstance(validation, dict) or validation.get("status") == "fail":
            outcome = {
                "status": "failed",
                "attempts": 1,
                "max_attempts": MAX_REPAIR_ATTEMPTS,
                "reason": "revalidation_failed",
                "revalidation_reason": (
                    validation.get("reason") if isinstance(validation, dict) else "invalid_revalidation_result"
                ),
                "failed_criterion": failed_criterion or None,
            }
            original["bounded_repair"] = outcome
            return original, outcome

        outcome = {
            "status": "repaired",
            "attempts": 1,
            "max_attempts": MAX_REPAIR_ATTEMPTS,
            "failed_criterion": failed_criterion or None,
            "revalidation_status": validation.get("status"),
        }
        candidate_payload["bounded_repair"] = outcome
        return candidate_payload, outcome
    except Exception as exc:
        outcome = {
            "status": "failed",
            "attempts": 1,
            "max_attempts": MAX_REPAIR_ATTEMPTS,
            "reason": "repair_validation_exception",
            "failure_type": type(exc).__name__,
            "failed_criterion": failed_criterion or None,
        }
        original["bounded_repair"] = outcome
        return original, outcome
