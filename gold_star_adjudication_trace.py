"""Privacy-minimized observability contract for runtime Gold Star adjudication.

This module deliberately distinguishes retrieval, prompt exposure, adjudication
selection, application evidence, and reviewed outcome. A candidate being retrieved
or injected into a provider prompt is never labeled as applied or beneficial.

No visitor question, answer text, user identifier, or content hash is retained.
"""
from __future__ import annotations

from typing import Any, Mapping

VERSION = "1.0"


def build_adjudication_trace(contribution: Any) -> dict[str, Any]:
    """Return safe candidate metadata; selection/application remain unobserved."""
    if not isinstance(contribution, Mapping):
        return {
            "version": VERSION,
            "state": "no_candidates",
            "candidate_count": 0,
            "candidate_ids": [],
            "candidate_scores": [],
            "match_kinds": [],
            "selection": "not_applicable",
            "application": "not_observed",
            "outcome": "not_evaluated",
        }

    candidates = contribution.get("candidates")
    if not isinstance(candidates, list):
        candidates = []
    safe_candidates = []
    seen = set()
    for candidate in candidates[:3]:
        if not isinstance(candidate, Mapping):
            continue
        benchmark_id = str(candidate.get("benchmark_id") or "").strip()
        if not benchmark_id or benchmark_id in seen:
            continue
        seen.add(benchmark_id)
        try:
            score = float(candidate.get("score"))
        except (TypeError, ValueError):
            score = None
        if score is not None and not 0.0 <= score <= 1.0:
            score = None
        safe_candidates.append({
            "benchmark_id": benchmark_id,
            "score": score,
            "match_kind": "exact" if candidate.get("exact") is True else "cross_question",
        })

    return {
        "version": VERSION,
        "state": "candidates_supplied" if safe_candidates else "no_candidates",
        "candidate_count": len(safe_candidates),
        "candidate_ids": [item["benchmark_id"] for item in safe_candidates],
        "candidate_scores": [item["score"] for item in safe_candidates],
        "match_kinds": [item["match_kind"] for item in safe_candidates],
        "selection": "not_observed",
        "application": "not_observed",
        "outcome": "not_evaluated",
    }


def mark_composition_result(
    trace: Mapping[str, Any],
    *,
    provider_result: Any,
) -> dict[str, Any]:
    """Record route completion without inferring semantic application."""
    result = dict(trace)
    parsed = provider_result.get("parsed") if isinstance(provider_result, Mapping) else None
    successful = isinstance(parsed, Mapping) and bool(str(parsed.get("response") or "").strip())
    if not isinstance(parsed, Mapping) and isinstance(provider_result, Mapping):
        successful = bool(str(provider_result.get("response") or "").strip())
    result["composition"] = "provider_candidate_returned" if successful else "provider_no_result"
    result["selection"] = "not_observed"
    result["application"] = "not_observed"
    result["outcome"] = "not_evaluated"
    return result


def mark_final_delivery(
    trace: Mapping[str, Any],
    *,
    provider_candidate_delivered: bool,
    final_provenance: str,
) -> dict[str, Any]:
    """Attach final answer provenance without awarding quality credit."""
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
    """Validate the privacy and evidence-stage boundary of an audit trace."""
    if not isinstance(trace, Mapping):
        return {"valid": False, "reason": "not_object"}
    required = {
        "version", "state", "candidate_count", "candidate_ids",
        "candidate_scores", "match_kinds", "selection", "application",
        "outcome",
    }
    missing = sorted(required - set(trace))
    if missing:
        return {"valid": False, "reason": "missing_fields", "missing": missing}
    if trace.get("version") != VERSION:
        return {"valid": False, "reason": "unsupported_version"}
    count = trace.get("candidate_count")
    ids = trace.get("candidate_ids")
    scores = trace.get("candidate_scores")
    kinds = trace.get("match_kinds")
    if not isinstance(count, int) or not 0 <= count <= 3:
        return {"valid": False, "reason": "invalid_candidate_count"}
    if not all(isinstance(value, list) and len(value) == count for value in (ids, scores, kinds)):
        return {"valid": False, "reason": "candidate_metadata_length_mismatch"}
    if len(set(ids)) != len(ids) or not all(isinstance(value, str) and value for value in ids):
        return {"valid": False, "reason": "invalid_candidate_ids"}
    if not all(value is None or (isinstance(value, (float, int)) and 0.0 <= value <= 1.0) for value in scores):
        return {"valid": False, "reason": "invalid_candidate_scores"}
    if not all(value in {"exact", "cross_question"} for value in kinds):
        return {"valid": False, "reason": "invalid_match_kinds"}
    if trace.get("selection") not in {"not_applicable", "not_observed", "human_reviewed_selected", "human_reviewed_rejected"}:
        return {"valid": False, "reason": "invalid_selection_state"}
    if trace.get("application") not in {"not_observed", "review_required", "human_reviewed_applied", "human_reviewed_not_applied"}:
        return {"valid": False, "reason": "invalid_application_state"}
    if trace.get("outcome") not in {"not_evaluated", "review_required", "human_reviewed_improved", "human_reviewed_not_improved"}:
        return {"valid": False, "reason": "invalid_outcome_state"}
    forbidden = {"query", "question", "answer", "response", "user_id", "session_id", "content_hash"}
    if forbidden.intersection(trace):
        return {"valid": False, "reason": "content_or_identity_field_prohibited"}
    return {"valid": True, "reason": "valid_not_quality_certified"}
