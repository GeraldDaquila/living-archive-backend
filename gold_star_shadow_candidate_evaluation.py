"""Evaluation-only shadow candidate derived from an immutable approved exemplar.

This module is deliberately separate from the production lesson registry and
selector. It exposes structural guidance only inside an explicit matched-pair
treatment context; it cannot grant runtime transfer, exact-answer authority,
or deterministic fallback.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inquiry_family_transfer_contract import classify_inquiry_family

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "docs" / "qa" / "gold_star_shadow_evaluation_candidates.json"
DEFAULT_CANDIDATE_ID = "shadow-metaphysical-distress-principles-2026-11-27"


def _load_candidate(candidate_id: str) -> dict[str, Any] | None:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise ValueError("Shadow evaluation candidate manifest is invalid.")
    matches = [item for item in entries if isinstance(item, dict) and item.get("candidate_id") == candidate_id]
    if len(matches) != 1:
        return None
    candidate = matches[0]
    if (
        candidate.get("evaluation_only") is not True
        or candidate.get("production_selector_visible") is not False
        or candidate.get("runtime_transfer") is not False
        or candidate.get("deterministic_fallback_eligible") is not False
        or candidate.get("exact_answer_authority") is not False
    ):
        raise ValueError("Shadow evaluation candidate exceeds its non-production capability boundary.")
    fixture_path = ROOT / str(candidate.get("source_fixture_path") or "")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if (
        fixture.get("benchmark_id") != candidate.get("source_benchmark_id")
        or fixture.get("freeze_policy") != "immutable_user_approved_gold_standard"
        or fixture.get("runtime_transfer") is not False
        or fixture.get("exact_answer_authority") is not False
        or fixture.get("deterministic_fallback_eligible") is not False
    ):
        raise ValueError("Shadow candidate source fixture is not the expected immutable non-runtime exemplar.")
    source_boundary = str(fixture.get("gold_star_capabilities", {}).get("abstention_boundary") or "").strip()
    evaluation_boundary = str(candidate.get("evaluation_abstention_boundary") or "").strip()
    if not source_boundary or not evaluation_boundary:
        raise ValueError("Shadow candidate source or evaluation boundary is missing.")
    return {
        **candidate,
        "source_query": str(fixture.get("query") or ""),
        "transferable_discipline": fixture.get("transferable_lesson", ""),
        "source_governance_boundary": source_boundary,
        "abstention_boundary": evaluation_boundary,
    }


def evaluation_only_candidate_contribution(query: str, candidate_id: str) -> dict[str, Any] | None:
    """Return one scoped candidate only for an explicit evaluation treatment."""
    candidate = _load_candidate(str(candidate_id or "").strip())
    if candidate is None:
        return None
    inquiry = classify_inquiry_family(query)
    if inquiry.get("family") not in set(candidate.get("allowed_inquiry_families") or []):
        return None
    discipline = str(candidate.get("transferable_discipline") or "").strip()
    boundary = str(candidate.get("abstention_boundary") or "").strip()
    if not discipline or not boundary:
        return None
    item = {
        "benchmark_id": candidate["source_benchmark_id"],
        "score": None,
        "exact": False,
        "match_basis": "evaluation_only_shadow_candidate",
        "role": "CONDITIONAL",
        "evaluation_only": True,
        "activation_condition": candidate["qualifying_context"],
        "query": candidate["source_query"],
        "known_theme": candidate["known_theme"],
        "reasoning_family": candidate["reasoning_family"],
        "discipline": discipline,
        "abstention_boundary": boundary,
    }
    return {
        "benchmark_id": item["benchmark_id"],
        "reasoning_family": item["reasoning_family"],
        "discipline": discipline,
        "abstention_boundary": boundary,
        "score": None,
        "exact": False,
        "authority_mode": "structural_guidance_only",
        "evaluation_only": True,
        "evaluation_candidate_id": candidate["candidate_id"],
        "runtime_transfer": False,
        "deterministic_fallback_eligible": False,
        "exact_answer_authority": False,
        "candidates": [item],
    }
