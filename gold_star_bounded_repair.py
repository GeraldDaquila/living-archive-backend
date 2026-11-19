"""Eligibility gate for one bounded, evidence-directed composition repair."""
from __future__ import annotations

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
        "max_attempts": MAX_REPAIR_ATTEMPTS,
        "semantic_certification": False,
    }
