"""Privacy-minimized observability contract for runtime Gold Star adjudication.

Retrieval, prompt exposure, model/provider completion, final delivery, human
review, and improvement are distinct evidence states. The system never labels
retrieval or prompt injection as lesson selection, application, or benefit.

No visitor question, answer text, user identity, session identity, or content
hash is retained in this trace.
"""
from __future__ import annotations

from typing import Any, Mapping
import re
from contextvars import ContextVar

VERSION = "1.1"
REQUEST_LEDGER_VERSION = "2"
MAX_CANDIDATES = 4
_SELECTION_STATES = {"not_applicable", "not_observed", "provider_reported_selected", "provider_reported_rejected_all", "deterministic_renderer_selected", "human_reviewed_selected", "human_reviewed_rejected"}
_APPLICATION_STATES = {"not_observed", "provider_asserted_span_present", "deterministic_renderer_applied", "review_required", "human_reviewed_applied", "human_reviewed_not_applied"}
_OUTCOME_STATES = {"not_evaluated", "review_required", "human_reviewed_improved", "human_reviewed_not_improved"}
_FORBIDDEN_KEYS = {"query", "question", "answer", "response", "user_id", "session_id", "content_hash"}
_REQUEST_CONTEXT = ContextVar("gold_star_request_context", default=None)
_CURRENT_ATTEMPT_TRACE = ContextVar("gold_star_current_attempt_trace", default=None)
_REQUEST_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def begin_request_context(request_id: str):
    """Start one opaque, request-local ledger context; caller owns reset."""
    value = str(request_id or "")
    if not _REQUEST_ID_PATTERN.fullmatch(value):
        raise ValueError("Gold Star request correlation token must be 32 lowercase hex characters.")
    request_token = _REQUEST_CONTEXT.set({
        "request_id": value,
        "composition_attempt_count": 0,
        "current_attempt_ordinal": None,
        "provider_route_count": 0,
        "provider_attempt_count": 0,
        "provider_success_count": 0,
        "provider_failure_count": 0,
        "provider_admission_denied_count": 0,
        "provider_terminal_state": "not_observed",
        "current_provider_route": None,
    })
    trace_token = _CURRENT_ATTEMPT_TRACE.set(None)
    return request_token, trace_token


def end_request_context(tokens) -> None:
    """Restore the previous context after the outer request boundary completes."""
    request_token, trace_token = tokens
    _CURRENT_ATTEMPT_TRACE.reset(trace_token)
    _REQUEST_CONTEXT.reset(request_token)


def begin_composition_attempt():
    """Count a composer attempt inside the active visitor request, if present."""
    state = _REQUEST_CONTEXT.get()
    _CURRENT_ATTEMPT_TRACE.set(None)
    if not isinstance(state, dict):
        return None
    state["current_provider_route"] = None
    state["composition_attempt_count"] = int(state.get("composition_attempt_count") or 0) + 1
    ordinal = state["composition_attempt_count"]
    state["current_attempt_ordinal"] = ordinal
    return {"request_id": state["request_id"], "attempt_ordinal": ordinal}


def current_request_context() -> dict:
    """Return only fixed, content-free request-ledger fields and counters."""
    state = _REQUEST_CONTEXT.get()
    if not isinstance(state, dict):
        return {
            "request_id": None,
            "request_ledger_version": REQUEST_LEDGER_VERSION,
            "composition_attempt_count": 0,
            "provider_route_count": 0,
            "provider_attempt_count": 0,
            "provider_success_count": 0,
            "provider_failure_count": 0,
            "provider_admission_denied_count": 0,
            "provider_terminal_state": "not_observed",
        }
    return {
        "request_id": state.get("request_id"),
        "request_ledger_version": REQUEST_LEDGER_VERSION,
        "composition_attempt_count": int(state.get("composition_attempt_count") or 0),
        "provider_route_count": int(state.get("provider_route_count") or 0),
        "provider_attempt_count": int(state.get("provider_attempt_count") or 0),
        "provider_success_count": int(state.get("provider_success_count") or 0),
        "provider_failure_count": int(state.get("provider_failure_count") or 0),
        "provider_admission_denied_count": int(state.get("provider_admission_denied_count") or 0),
        "provider_terminal_state": str(state.get("provider_terminal_state") or "not_observed"),
    }


def current_attempt_trace():
    """Return the current composition attempt's private trace, if initialized."""
    value = _CURRENT_ATTEMPT_TRACE.get()
    return dict(value) if isinstance(value, Mapping) else None


_PROVIDER_ROUTE_TERMINAL_STATES = {
    "provider_succeeded",
    "counterpart_success",
    "provider_exhausted",
    "no_eligible_candidate",
    "budget_skipped",
    "admission_blocked",
    "provider_not_attempted",
    "provider_exception",
}


def begin_provider_route(operation: str):
    """Begin a correlated Guide provider route inside the current composer attempt."""
    if str(operation or "") != "general_guide_composition":
        return None
    state = _REQUEST_CONTEXT.get()
    attempt = _CURRENT_ATTEMPT_TRACE.get()
    if not isinstance(state, dict) or not isinstance(attempt, Mapping):
        return None
    request_id = state.get("request_id")
    attempt_ordinal = attempt.get("attempt_ordinal")
    if not request_id or not isinstance(attempt_ordinal, int):
        return None
    route_ordinal = int(state.get("provider_route_count") or 0) + 1
    route = {
        "request_id": request_id,
        "request_ledger_version": REQUEST_LEDGER_VERSION,
        "attempt_ordinal": attempt_ordinal,
        "provider_route_ordinal": route_ordinal,
        "eligible_candidate_count": None,
        "attempt_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "admission_denied_count": 0,
        "terminal_state": "in_progress",
        "active": True,
    }
    state["provider_route_count"] = route_ordinal
    state["current_provider_route"] = route
    return dict(route)


def _current_provider_route(operation: str):
    if str(operation or "") != "general_guide_composition":
        return None
    state = _REQUEST_CONTEXT.get()
    route = state.get("current_provider_route") if isinstance(state, dict) else None
    return route if isinstance(route, dict) else None


def set_provider_route_candidate_count(operation: str, count: int) -> None:
    """Record the number of eligible local candidates before provider attempts."""
    route = _current_provider_route(operation)
    if route is not None:
        route["eligible_candidate_count"] = max(0, int(count or 0))


def record_provider_candidate_attempt(operation: str) -> None:
    """Count an actual outbound candidate call, not a skipped/admission-blocked lane."""
    route = _current_provider_route(operation)
    state = _REQUEST_CONTEXT.get()
    if route is None or not isinstance(state, dict):
        return
    route["attempt_count"] += 1
    state["provider_attempt_count"] = int(state.get("provider_attempt_count") or 0) + 1


def record_provider_candidate_outcome(operation: str, outcome: str) -> None:
    """Record one bounded candidate outcome for the current Guide provider route."""
    route = _current_provider_route(operation)
    state = _REQUEST_CONTEXT.get()
    if route is None or not isinstance(state, dict):
        return
    value = str(outcome or "")
    if value == "success":
        route["success_count"] += 1
        state["provider_success_count"] = int(state.get("provider_success_count") or 0) + 1
    elif value == "failure":
        route["failure_count"] += 1
        state["provider_failure_count"] = int(state.get("provider_failure_count") or 0) + 1
    elif value == "admission_denied":
        route["admission_denied_count"] += 1
        state["provider_admission_denied_count"] = int(state.get("provider_admission_denied_count") or 0) + 1


def finish_provider_route(operation: str, terminal_state: str):
    """Close one provider route with a fixed terminal classification."""
    route = _current_provider_route(operation)
    state = _REQUEST_CONTEXT.get()
    if route is None or not isinstance(state, dict):
        return {}
    value = str(terminal_state or "")
    route["terminal_state"] = value if value in _PROVIDER_ROUTE_TERMINAL_STATES else "provider_exception"
    route["active"] = False
    state["provider_terminal_state"] = route["terminal_state"]
    return dict(route)


def current_provider_route_context() -> dict:
    """Return the current provider route's content-free correlation and counters."""
    route = _current_provider_route("general_guide_composition")
    return dict(route) if isinstance(route, dict) else {}


def _store_current_trace(value):
    if isinstance(value, Mapping):
        _CURRENT_ATTEMPT_TRACE.set(dict(value))
    return value


def build_adjudication_trace(contribution: Any) -> dict[str, Any]:
    """Build a trace of retrieved candidates without implying a model verdict."""
    candidates = contribution.get("candidates") if isinstance(contribution, Mapping) else None
    candidates = candidates if isinstance(candidates, list) else []
    safe_candidates = []
    seen = set()
    for item in candidates[:MAX_CANDIDATES]:
        if not isinstance(item, Mapping):
            continue
        benchmark_id = str(item.get("benchmark_id") or "").strip()
        if not benchmark_id or benchmark_id in seen:
            continue
        seen.add(benchmark_id)
        try:
            score = float(item.get("score"))
        except (TypeError, ValueError):
            score = None
        if score is not None and not 0.0 <= score <= 1.0:
            score = None
        safe_candidates.append({
            "benchmark_id": benchmark_id,
            "score": score,
            "match_kind": "governed_policy" if item.get("match_basis") == "governed_decision_rights_policy" else ("exact" if item.get("exact") is True else "cross_question"),
        })
    count = len(safe_candidates)
    result = {
        "version": VERSION,
        "state": "candidates_supplied" if count else "no_candidates",
        "candidate_count": count,
        "candidate_ids": [item["benchmark_id"] for item in safe_candidates],
        "candidate_scores": [item["score"] for item in safe_candidates],
        "match_kinds": [item["match_kind"] for item in safe_candidates],
        "guidance_exposure": "pending" if count else "not_applicable",
        "provider_adjudication_status": "not_observed",
        "selected_candidate_ids": [],
        "rejection_reason_codes": [],
        "reasoning_discipline_ids": [],
        "application_evidence_present": False,
        "application_evidence_candidate_ids": [],
        "contribution_retained": "not_evaluated",
        "selection": "not_observed" if count else "not_applicable",
        "application": "not_observed",
        "outcome": "not_evaluated",
    }
    request = _REQUEST_CONTEXT.get()
    if isinstance(request, dict):
        result["request_id"] = request["request_id"]
        result["attempt_ordinal"] = request.get("current_attempt_ordinal")
    _CURRENT_ATTEMPT_TRACE.set(result)
    return result


def mark_guidance_exposure(trace: Mapping[str, Any], *, included_in_provider_prompt: bool) -> dict[str, Any]:
    """Record prompt exposure only; exposure is not evidence of model selection or use."""
    result = dict(trace)
    if not result.get("candidate_count"):
        result["guidance_exposure"] = "not_applicable"
    else:
        result["guidance_exposure"] = (
            "included_in_provider_prompt" if included_in_provider_prompt else "not_included"
        )
    return _store_current_trace(result)


def mark_provider_adjudication(trace: Mapping[str, Any], result: Any) -> dict[str, Any]:
    """Attach a validated provider report without promoting it to human evidence."""
    updated = dict(trace)
    if not isinstance(result, Mapping):
        return _store_current_trace(updated)
    allowed = {
        "status", "selected_candidate_ids", "rejection_reason_codes",
        "reasoning_discipline_ids", "application_evidence_present", "application_evidence_candidate_ids", "application",
    }
    if set(result) != allowed:
        return _store_current_trace(updated)
    updated["provider_adjudication_status"] = result["status"]
    updated["selected_candidate_ids"] = list(result["selected_candidate_ids"])
    updated["rejection_reason_codes"] = list(result["rejection_reason_codes"])
    updated["reasoning_discipline_ids"] = list(result["reasoning_discipline_ids"])
    updated["application_evidence_present"] = result["application_evidence_present"] is True
    updated["application_evidence_candidate_ids"] = list(result["application_evidence_candidate_ids"])
    updated["application"] = result["application"]
    return _store_current_trace(updated)


def mark_composition_result(trace: Mapping[str, Any], *, provider_result: Any) -> dict[str, Any]:
    """Record whether the provider returned a candidate answer, not whether it applied a lesson."""
    result = dict(trace)
    parsed = provider_result.get("parsed") if isinstance(provider_result, Mapping) else None
    returned = (
        bool(str(parsed.get("response") or "").strip())
        if isinstance(parsed, Mapping)
        else bool(str(provider_result.get("response") or "").strip())
        if isinstance(provider_result, Mapping)
        else False
    )
    result["composition"] = "provider_candidate_returned" if returned else "provider_no_result"
    if result.get("provider_adjudication_status") == "provider_reported_selected":
        result["selection"] = "provider_reported_selected"
    elif result.get("provider_adjudication_status") == "provider_reported_rejected_all":
        result["selection"] = "provider_reported_rejected_all"
    else:
        result["selection"] = "not_observed" if result.get("candidate_count", 0) else "not_applicable"
    if result.get("provider_adjudication_status") == "not_observed" and result.get("selection") != "deterministic_renderer_selected":
        result["application"] = "not_observed"
    result["outcome"] = "not_evaluated"
    return _store_current_trace(result)


def mark_deterministic_application(trace: Any, application: Any) -> dict[str, Any] | None:
    """Record a verified local renderer application without claiming provider selection.

    The renderer must return a candidate already present in this request's
    bounded retrieval trace, a registered plan, evidence spans, and an applied
    abstention boundary. Provider adjudication remains independently observed.
    """
    if not isinstance(trace, Mapping) or not isinstance(application, Mapping):
        return _store_current_trace(trace) if isinstance(trace, Mapping) else None
    benchmark_id = str(application.get("benchmark_id") or "").strip()
    plan_id = str(application.get("plan_id") or "").strip()
    spans = application.get("application_evidence_spans")
    if (
        not benchmark_id
        or benchmark_id not in (trace.get("candidate_ids") or [])
        or not plan_id
        or application.get("abstention_boundary_applied") is not True
        or not isinstance(spans, list)
        or not spans
        or not all(isinstance(span, str) and span.strip() for span in spans)
    ):
        return _store_current_trace(dict(trace))
    result = dict(trace)
    result["selection"] = "deterministic_renderer_selected"
    result["selected_candidate_ids"] = [benchmark_id]
    result["reasoning_discipline_ids"] = [plan_id]
    result["application_evidence_present"] = True
    result["application_evidence_candidate_ids"] = [benchmark_id]
    result["application"] = "deterministic_renderer_applied"
    result["deterministic_application_span_count"] = len(spans)
    return _store_current_trace(result)


def mark_cache_reuse(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Create current-request evidence for a cache hit without inheriting old adjudication."""
    result = dict(trace)
    result["provider_adjudication_status"] = "not_observed"
    result["selected_candidate_ids"] = []
    result["rejection_reason_codes"] = []
    result["reasoning_discipline_ids"] = []
    result["application_evidence_present"] = False
    result["application_evidence_candidate_ids"] = []
    result["selection"] = "not_observed" if result.get("candidate_count", 0) else "not_applicable"
    result["application"] = "not_observed"
    result["composition"] = "cached_candidate_reused"
    result["contribution_retained"] = "not_evaluated"
    result["outcome"] = "not_evaluated"
    return _store_current_trace(result)



def synchronize_final_response_provenance(
    payload: Any,
    *,
    final_provenance: str,
    provider_candidate_delivered: bool,
    cached_candidate_reused: bool,
) -> Any:
    """Make public provenance describe the answer that survived final boundaries.

    Provider invocation metadata is retained as historical route evidence, but
    a deterministic rewrite must not leave the delivered answer labeled as LLM.
    """
    if not isinstance(payload, dict):
        return payload
    if provider_candidate_delivered or cached_candidate_reused:
        return payload
    allowed = {"deterministic_by_design", "deterministic_recovery", "unresolved"}
    provenance_class = (
        final_provenance if final_provenance in allowed else "unresolved"
    )
    provenance = payload.get("response_provenance")
    provenance = dict(provenance) if isinstance(provenance, Mapping) else {}
    provenance["class"] = provenance_class
    payload["response_provenance"] = provenance
    return payload


def mark_final_delivery(
    trace: Mapping[str, Any], *, provider_candidate_delivered: bool,
    final_provenance: str, cached_candidate_reused: bool = False
) -> dict[str, Any]:
    """Attach final delivery attribution; delivery is not evidence of quality."""
    result = dict(trace)
    result["final_delivery"] = (
        "cached_candidate_reused" if cached_candidate_reused
        else "provider_candidate_delivered" if provider_candidate_delivered
        else "deterministic_or_unresolved_replacement"
    )
    result["final_provenance"] = str(final_provenance or "unresolved").strip().casefold()
    result["contribution_retained"] = (
        "not_applicable" if result.get("provider_adjudication_status") == "provider_reported_rejected_all"
        else "provider_asserted_span_retained" if provider_candidate_delivered and result.get("application_evidence_present") is True
        else "not_retained" if not provider_candidate_delivered and not cached_candidate_reused
        else "not_verified"
    )
    result["outcome"] = "not_evaluated"
    return _store_current_trace(result)


def validate_trace(trace: Any) -> dict[str, Any]:
    """Validate allowed fields, metadata lengths, and epistemic stage labels."""
    if not isinstance(trace, Mapping):
        return {"valid": False, "reason": "not_object"}
    if _FORBIDDEN_KEYS.intersection(trace):
        return {"valid": False, "reason": "content_or_identity_field_prohibited"}
    required = {
        "version", "state", "candidate_count", "candidate_ids",
        "candidate_scores", "match_kinds", "selection", "application", "outcome",
    }
    missing = sorted(required - set(trace))
    if missing:
        return {"valid": False, "reason": "missing_fields", "missing": missing}
    allowed = required | {
        "guidance_exposure", "provider_adjudication_status", "selected_candidate_ids",
        "rejection_reason_codes", "reasoning_discipline_ids", "application_evidence_present",
        "application_evidence_candidate_ids", "contribution_retained", "composition",
        "deterministic_application_span_count", "final_delivery", "final_provenance",
        "request_id", "attempt_ordinal"
    }
    unexpected = sorted(set(trace) - allowed)
    if unexpected:
        return {"valid": False, "reason": "unexpected_fields", "fields": unexpected}
    if trace.get("version") != VERSION:
        return {"valid": False, "reason": "unsupported_version"}
    if "request_id" in trace and (
        not isinstance(trace.get("request_id"), str)
        or not _REQUEST_ID_PATTERN.fullmatch(trace["request_id"])
    ):
        return {"valid": False, "reason": "invalid_request_correlation_token"}
    if "attempt_ordinal" in trace and (
        type(trace.get("attempt_ordinal")) is not int or trace["attempt_ordinal"] < 1
    ):
        return {"valid": False, "reason": "invalid_composition_attempt_ordinal"}
    count = trace.get("candidate_count")
    ids, scores, kinds = trace.get("candidate_ids"), trace.get("candidate_scores"), trace.get("match_kinds")
    if type(count) is not int or not 0 <= count <= MAX_CANDIDATES:
        return {"valid": False, "reason": "invalid_candidate_count"}
    if not all(isinstance(value, list) and len(value) == count for value in (ids, scores, kinds)):
        return {"valid": False, "reason": "candidate_metadata_length_mismatch"}
    if not all(isinstance(value, str) and value for value in ids) or len(set(ids)) != count:
        return {"valid": False, "reason": "invalid_candidate_ids"}
    if not all(value is None or (type(value) in (int, float) and 0.0 <= value <= 1.0) for value in scores):
        return {"valid": False, "reason": "invalid_candidate_scores"}
    if not all(value in {"exact", "cross_question", "governed_policy"} for value in kinds):
        return {"valid": False, "reason": "invalid_match_kinds"}
    if trace.get("selection") not in _SELECTION_STATES:
        return {"valid": False, "reason": "invalid_selection_state"}
    if trace.get("application") not in _APPLICATION_STATES:
        return {"valid": False, "reason": "invalid_application_state"}
    if trace.get("outcome") not in _OUTCOME_STATES:
        return {"valid": False, "reason": "invalid_outcome_state"}
    if "guidance_exposure" in trace and trace["guidance_exposure"] not in {
        "pending", "not_applicable", "included_in_provider_prompt", "not_included"
    }:
        return {"valid": False, "reason": "invalid_guidance_exposure_state"}
    if trace.get("provider_adjudication_status", "not_observed") not in {
        "not_observed", "provider_reported_selected", "provider_reported_rejected_all"
    }:
        return {"valid": False, "reason": "invalid_provider_adjudication_status"}
    selected_ids = trace.get("selected_candidate_ids", [])
    rejections = trace.get("rejection_reason_codes", [])
    disciplines = trace.get("reasoning_discipline_ids", [])
    if not isinstance(selected_ids, list) or len(selected_ids) > count or any(x not in ids for x in selected_ids):
        return {"valid": False, "reason": "invalid_selected_candidate_ids"}
    if not isinstance(rejections, list) or len(rejections) > count or not all(
        isinstance(x, Mapping) and set(x) == {"candidate_id", "reason_code"}
        and x["candidate_id"] in ids and x["reason_code"] in {"subject_mismatch", "lexical_overlap_only", "redundant_contribution", "boundary_mismatch", "conflicting_discipline", "insufficient_relevance", "no_distinct_contribution"}
        for x in rejections
    ):
        return {"valid": False, "reason": "invalid_rejection_reason_codes"}
    if not isinstance(disciplines, list) or len(disciplines) > count or not all(
        isinstance(x, str) and x for x in disciplines
    ):
        return {"valid": False, "reason": "invalid_reasoning_discipline_ids"}
    if type(trace.get("application_evidence_present", False)) is not bool:
        return {"valid": False, "reason": "invalid_application_evidence_state"}
    if trace.get("contribution_retained", "not_evaluated") not in {
        "not_evaluated", "not_applicable", "provider_asserted_span_retained", "not_retained", "not_verified"
    }:
        return {"valid": False, "reason": "invalid_contribution_retention_state"}
    rejection_ids = [item["candidate_id"] for item in rejections]
    if len(set(rejection_ids)) != len(rejection_ids) or set(selected_ids) & set(rejection_ids):
        return {"valid": False, "reason": "duplicate_or_conflicting_candidate_disposition"}
    adjudication_status = trace.get("provider_adjudication_status", "not_observed")
    if adjudication_status == "provider_reported_selected" and (
        not selected_ids or set(selected_ids) | set(rejection_ids) != set(ids) or not disciplines
    ):
        return {"valid": False, "reason": "incomplete_selected_candidate_adjudication"}
    if adjudication_status == "provider_reported_rejected_all" and (
        selected_ids or set(rejection_ids) != set(ids) or disciplines
    ):
        return {"valid": False, "reason": "incomplete_reject_all_adjudication"}
    evidence_ids = trace.get("application_evidence_candidate_ids", [])
    if not isinstance(evidence_ids, list) or len(evidence_ids) > count or any(
        candidate_id not in selected_ids for candidate_id in evidence_ids
    ) or len(set(evidence_ids)) != len(evidence_ids):
        return {"valid": False, "reason": "invalid_application_evidence_candidate_ids"}
    if trace.get("application_evidence_present") is True and (
        not selected_ids or set(evidence_ids) != set(selected_ids)
    ):
        return {"valid": False, "reason": "application_span_without_complete_selected_candidate_coverage"}
    if trace.get("application_evidence_present") is not True and evidence_ids:
        return {"valid": False, "reason": "application_evidence_ids_without_verified_spans"}
    if trace.get("selection") == "deterministic_renderer_selected" and (
        trace.get("provider_adjudication_status") != "not_observed"
        or trace.get("application") != "deterministic_renderer_applied"
        or trace.get("application_evidence_present") is not True
        or len(selected_ids) != 1
        or evidence_ids != selected_ids
        or type(trace.get("deterministic_application_span_count")) is not int
        or trace["deterministic_application_span_count"] < 1
    ):
        return {"valid": False, "reason": "incomplete_deterministic_renderer_application"}
    if trace.get("application") == "deterministic_renderer_applied" and (
        trace.get("selection") != "deterministic_renderer_selected"
    ):
        return {"valid": False, "reason": "deterministic_application_without_renderer_selection"}
    if trace.get("contribution_retained") == "provider_asserted_span_retained" and (
        trace.get("final_delivery") != "provider_candidate_delivered"
        or trace.get("application_evidence_present") is not True
    ):
        return {"valid": False, "reason": "retention_claim_without_delivered_verified_span"}
    if "composition" in trace and trace["composition"] not in {"provider_candidate_returned", "provider_no_result", "cached_candidate_reused"}:
        return {"valid": False, "reason": "invalid_composition_state"}
    if "final_delivery" in trace and trace["final_delivery"] not in {
        "provider_candidate_delivered", "cached_candidate_reused", "deterministic_or_unresolved_replacement"
    }:
        return {"valid": False, "reason": "invalid_final_delivery_state"}
    if "final_provenance" in trace and trace["final_provenance"] not in {
        "llm", "deterministic_by_design", "deterministic_recovery", "unresolved"
    }:
        return {"valid": False, "reason": "invalid_final_provenance"}
    if trace.get("state") not in {"no_candidates", "candidates_supplied"}:
        return {"valid": False, "reason": "invalid_trace_state"}
    return {"valid": True, "reason": "valid_not_quality_certified"}
