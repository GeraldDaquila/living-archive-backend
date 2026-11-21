"""Privacy-minimized observability contract for runtime Gold Star adjudication.

Retrieval, prompt exposure, model/provider completion, final delivery, human
review, and improvement are distinct evidence states. The system never labels
retrieval or prompt injection as lesson selection, application, or benefit.

No visitor question, answer text, user identity, session identity, or content
hash is retained in this trace.
"""
from __future__ import annotations

from typing import Any, Mapping

VERSION = "1.0"
MAX_CANDIDATES = 3
_SELECTION_STATES = {"not_applicable", "not_observed", "provider_reported_selected", "provider_reported_rejected_all", "human_reviewed_selected", "human_reviewed_rejected"}
_APPLICATION_STATES = {"not_observed", "provider_asserted_span_present", "review_required", "human_reviewed_applied", "human_reviewed_not_applied"}
_OUTCOME_STATES = {"not_evaluated", "review_required", "human_reviewed_improved", "human_reviewed_not_improved"}
_FORBIDDEN_KEYS = {"query", "question", "answer", "response", "user_id", "session_id", "content_hash"}


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
            "match_kind": "exact" if item.get("exact") is True else "cross_question",
        })
    count = len(safe_candidates)
    return {
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


def mark_guidance_exposure(trace: Mapping[str, Any], *, included_in_provider_prompt: bool) -> dict[str, Any]:
    """Record prompt exposure only; exposure is not evidence of model selection or use."""
    result = dict(trace)
    if not result.get("candidate_count"):
        result["guidance_exposure"] = "not_applicable"
    else:
        result["guidance_exposure"] = (
            "included_in_provider_prompt" if included_in_provider_prompt else "not_included"
        )
    return result


def mark_provider_adjudication(trace: Mapping[str, Any], result: Any) -> dict[str, Any]:
    """Attach a validated provider report without promoting it to human evidence."""
    updated = dict(trace)
    if not isinstance(result, Mapping):
        return updated
    allowed = {
        "status", "selected_candidate_ids", "rejection_reason_codes",
        "reasoning_discipline_ids", "application_evidence_present", "application_evidence_candidate_ids", "application",
    }
    if set(result) != allowed:
        return updated
    updated["provider_adjudication_status"] = result["status"]
    updated["selected_candidate_ids"] = list(result["selected_candidate_ids"])
    updated["rejection_reason_codes"] = list(result["rejection_reason_codes"])
    updated["reasoning_discipline_ids"] = list(result["reasoning_discipline_ids"])
    updated["application_evidence_present"] = result["application_evidence_present"] is True
    updated["application_evidence_candidate_ids"] = list(result["application_evidence_candidate_ids"])
    updated["application"] = result["application"]
    return updated


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
    if result.get("provider_adjudication_status") == "not_observed":
        result["application"] = "not_observed"
    result["outcome"] = "not_evaluated"
    return result


def mark_final_delivery(
    trace: Mapping[str, Any], *, provider_candidate_delivered: bool, final_provenance: str
) -> dict[str, Any]:
    """Attach final delivery attribution; delivery is not evidence of quality."""
    result = dict(trace)
    result["final_delivery"] = (
        "provider_candidate_delivered"
        if provider_candidate_delivered
        else "deterministic_or_unresolved_replacement"
    )
    result["final_provenance"] = str(final_provenance or "unresolved").strip().casefold()
    result["contribution_retained"] = (
        "not_applicable" if result.get("provider_adjudication_status") == "provider_reported_rejected_all"
        else "provider_asserted_span_retained" if provider_candidate_delivered and result.get("application_evidence_present") is True
        else "not_retained" if not provider_candidate_delivered
        else "not_verified"
    )
    result["outcome"] = "not_evaluated"
    return result


def mark_evaluation_outcome(trace: Mapping[str, Any], evaluation: Any) -> dict[str, Any]:
    """Record only a complete, human-reviewed paired-batch evaluation result."""
    result = dict(trace)
    if not isinstance(evaluation, Mapping) or evaluation.get("valid") is not True:
        return result
    cases = evaluation.get("cases")
    paired_count = evaluation.get("paired_case_count")
    if (
        not isinstance(cases, list)
        or type(paired_count) is not int
        or paired_count < 1
        or len(cases) != paired_count
        or not all(isinstance(case, Mapping) and case.get("human_reviewed") is True for case in cases)
    ):
        return result
    status = evaluation.get("status")
    if (
        status == "eligible_for_human_promotion_review"
        and evaluation.get("human_promotion_approval_required") is True
        and evaluation.get("registry_mutated") is False
        and evaluation.get("regression_count") == 0
        and evaluation.get("case_family_count", 0) >= 2
        and evaluation.get("mean_score_delta", 0) > 0
    ):
        result["outcome"] = "human_reviewed_improved"
    elif status == "evidence_insufficient":
        if evaluation.get("regression_count", 0) > 0 or evaluation.get("mean_score_delta", 0) <= 0:
            result["outcome"] = "human_reviewed_not_improved"
        else:
            result["outcome"] = "review_required"
    return result


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
        "application_evidence_candidate_ids", "contribution_retained", "composition", "final_delivery", "final_provenance"
    }
    unexpected = sorted(set(trace) - allowed)
    if unexpected:
        return {"valid": False, "reason": "unexpected_fields", "fields": unexpected}
    if trace.get("version") != VERSION:
        return {"valid": False, "reason": "unsupported_version"}
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
    if not all(value in {"exact", "cross_question"} for value in kinds):
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
    if trace.get("contribution_retained") == "provider_asserted_span_retained" and (
        trace.get("final_delivery") != "provider_candidate_delivered"
        or trace.get("application_evidence_present") is not True
    ):
        return {"valid": False, "reason": "retention_claim_without_delivered_verified_span"}
    if "composition" in trace and trace["composition"] not in {"provider_candidate_returned", "provider_no_result"}:
        return {"valid": False, "reason": "invalid_composition_state"}
    if "final_delivery" in trace and trace["final_delivery"] not in {
        "provider_candidate_delivered", "deterministic_or_unresolved_replacement"
    }:
        return {"valid": False, "reason": "invalid_final_delivery_state"}
    if "final_provenance" in trace and trace["final_provenance"] not in {
        "llm", "deterministic_by_design", "deterministic_recovery", "unresolved"
    }:
        return {"valid": False, "reason": "invalid_final_provenance"}
    if trace.get("state") not in {"no_candidates", "candidates_supplied"}:
        return {"valid": False, "reason": "invalid_trace_state"}
    return {"valid": True, "reason": "valid_not_quality_certified"}
