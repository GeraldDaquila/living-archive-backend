"""Privacy-conscious, best-effort telemetry for Guide fuzzy shadow scoring.

This module observes the existing deterministic decision. It never returns a
score to the selector, persists data, or raises into the visitor request path.
Structured records go to the application's configured Python logger.
"""
import hashlib
import json
import logging

_LOGGER = logging.getLogger("guide.fuzzy_relevance.shadow")


def _digest(value):
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def record_shadow_comparison(*, query, candidates, selected):
    """Log bounded score diagnostics without raw visitor text or canonical URLs."""
    try:
        unique = {}
        for candidate in candidates or []:
            if not isinstance(candidate, dict):
                continue
            score = candidate.get("_fuzzy_relevance_shadow")
            if not isinstance(score, dict):
                continue
            url = str(candidate.get("url") or candidate.get("canonical_url") or "").strip()
            title = str(candidate.get("title") or "").strip()
            if not url or not title:
                continue
            key = _digest(url)
            unique[key] = {
                "resource_id": key,
                "score": {
                    str(name)[:48]: round(float(value), 4)
                    for name, value in score.items()
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                },
            }
        if not unique:
            return
        selected_url = str((selected or {}).get("url") or (selected or {}).get("canonical_url") or "").strip()
        selected_id = _digest(selected_url) if selected_url else None
        scored = [
            (resource_id, item["score"].get("overall_shadow_score", 0.0))
            for resource_id, item in unique.items()
        ]
        max_score = max((score for _, score in scored), default=None)
        selected_score = unique.get(selected_id, {}).get("score", {}).get("overall_shadow_score")
        record = {
            "event": "guide_fuzzy_relevance_shadow",
            "query_id": _digest(query),
            "candidate_count": len(unique),
            "selected_resource_id": selected_id,
            "selected_score": selected_score,
            "max_candidate_score": max_score,
            "selected_matches_fuzzy_max": (
                selected_score is not None and max_score is not None and selected_score == max_score
            ),
            "candidates": list(unique.values())[:30],
        }
        _LOGGER.info("%s", json.dumps(record, sort_keys=True, separators=(",", ":")))
    except Exception:
        # Shadow diagnostics must never influence visitor-facing behavior.
        return
