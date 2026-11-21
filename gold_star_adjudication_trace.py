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
_SELECTION_STATES = {"not_applicable", "not_observed", "human_reviewed_selected", "human_reviewed_rejected"}
_APPLICATION_STATES = {"not_observed", "review_required", "human_reviewed_applied", "human_reviewed_not_applied"}
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
        "selection": "not_observed" if count else "not_applicable",
        "application": "not_observed",
        "outcome": "not_evaluated",
    }


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
    result["selection"] = "not_observed" if result.get("candidate_count", 0) else "not_applicable"
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
    result["application"] = "not_observed"
    result["outcome"] = "not_evaluated"
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
    allowed = required | {"composition", "final_delivery", "final_provenance"}
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


def test_trace_builder_reports_candidate_retrieval_without_selecting_or_applying():
    result = build_adjudication_trace({
        "candidates": [
            {"benchmark_id": "lesson-one", "score": 0.83, "exact": False},
            {"benchmark_id": "lesson-two", "score": 0.72, "exact": True},
        ]
    })
    assert result["state"] == "candidates_supplied"
    assert result["selection"] == "not_observed"
    assert result["application"] == "not_observed"
    assert result["outcome"] == "not_evaluated"
    assert validate_trace(result)["valid"]


def test_provider_candidate_return_is_not_proof_of_application():
    initial = build_adjudication_trace({"candidates": [
        {"benchmark_id": "lesson-one", "score": 0.83, "exact": False}
    ]})
    result = mark_composition_result(
        initial, provider_result={"parsed": {"response": "A substantive answer."}}
    )
    assert result["composition"] == "provider_candidate_returned"
    assert result["selection"] == "not_observed"
    assert result["application"] == "not_observed"
    assert result["outcome"] == "not_evaluated"
    assert validate_trace(result)["valid"]


def test_final_deterministic_replacement_gets_no_provider_adaptation_credit():
    initial = build_adjudication_trace({"candidates": [
        {"benchmark_id": "lesson-one", "score": 0.83, "exact": False}
    ]})
    composed = mark_composition_result(
        initial, provider_result={"parsed": {"response": "Provider answer."}}
    )
    final = mark_final_delivery(
        composed,
        provider_candidate_delivered=False,
        final_provenance="deterministic_recovery",
    )
    assert final["final_delivery"] == "deterministic_or_unresolved_replacement"
    assert final["final_provenance"] == "deterministic_recovery"
    assert final["application"] == "not_observed"
    assert final["outcome"] == "not_evaluated"
    assert validate_trace(final)["valid"]


def test_trace_rejects_visitor_content_and_identity_fields():
    result = build_adjudication_trace(None)
    assert validate_trace({**result, "query": "private"}) == {
        "valid": False, "reason": "content_or_identity_field_prohibited"
    }
