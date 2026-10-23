"""Low-cost, startup-loaded answer-structure exemplars for the General Guide.

The governed QA registry remains the source of truth. This module reads it once
at process import, uses a small lexical matcher (no network/model call), and
returns at most one approved example as structural guidance. It never chooses
or copies a doorway and never replaces Archive evidence retrieval.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONTRACT_VERSION = "v1"
_REGISTRY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
_STOP_WORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "could",
    "did", "do", "does", "for", "from", "had", "has", "have", "how", "i",
    "if", "in", "into", "is", "it", "its", "me", "my", "of", "on", "or",
    "our", "should", "so", "that", "the", "their", "them", "there", "this",
    "to", "up", "was", "we", "what", "when", "where", "which", "who", "why",
    "will", "with", "would", "you", "your",
})
_ALLOWED_STATUSES = frozenset({
    "FROZEN_REFERENCE_ONLY",
    "USER_APPROVED_GOLD_STANDARD_PENDING_FIXTURE",
    "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT",
})


def _tokens(value: Any) -> set:
    words = re.findall(r"[a-z0-9]+", str(value or "").casefold())
    return {word for word in words if len(word) > 2 and word not in _STOP_WORDS}


def _response_for_record(record: Dict[str, Any]) -> str:
    response = record.get("expected_response")
    if not response:
        response = record.get("reconstruction_candidate_response")
    return str(response or "").strip()


def _load_exemplars() -> List[Dict[str, Any]]:
    try:
        payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        records = payload.get("records", [])
    except (OSError, ValueError, TypeError):
        # A missing or malformed optional registry must not stop Guide startup.
        return []
    result = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("subsystem") != "general-purpose-guide":
            continue
        if record.get("status") not in _ALLOWED_STATUSES:
            continue
        query = str(record.get("query") or "").strip()
        response = _response_for_record(record)
        terms = _tokens(query + " " + str(record.get("known_theme") or ""))
        assertions = record.get("assertions") or []
        if not query or not response or not terms:
            continue
        # The saved response is required as an approval gate but is deliberately
        # not sent into the prompt, avoiding copy pressure and excess token cost.
        known_theme = str(record.get("known_theme") or "").strip()
        structural_assertions = [
            str(item).strip() for item in assertions
            if isinstance(item, str) and str(item).strip()
        ][:3]
        result.append({
            "id": str(record.get("benchmark_id") or ""),
            "status": str(record.get("status") or ""),
            "query": query,
            "known_theme": known_theme,
            "assertions": structural_assertions,
            "terms": terms,
        })
    return result


# Read once at import; never fetch GitHub or parse the registry per visitor turn.
_EXEMPLARS = _load_exemplars()


def select_exemplar(query: str) -> Optional[Dict[str, Any]]:
    """Return a conservative best match, or None when lexical evidence is weak."""
    query_terms = _tokens(query)
    if len(query_terms) < 2:
        return None
    ranked: List[Tuple[float, int, Dict[str, Any]]] = []
    for exemplar in _EXEMPLARS:
        overlap = query_terms & exemplar["terms"]
        if len(overlap) < 2:
            continue
        # Dice similarity favours genuine shared topic terms while remaining
        # cheap and deterministic. No external embeddings or model call.
        score = (2.0 * len(overlap)) / (len(query_terms) + len(exemplar["terms"]))
        ranked.append((score, len(overlap), exemplar))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    score, overlap_count, exemplar = ranked[0]
    if score < 0.16 or overlap_count < 2:
        return None
    return {
        "benchmark_id": exemplar["id"],
        "status": exemplar["status"],
        "score": round(score, 3),
        "question": exemplar["query"],
        "known_theme": exemplar["known_theme"],
        "assertions": exemplar["assertions"],
    }


def build_exemplar_guidance(query: str) -> Tuple[str, str]:
    """Return prompt guidance and a cache-key token; empty when no safe match."""
    exemplar = select_exemplar(query)
    if not exemplar:
        return "", "none"
    guidance = (
        "Potentially relevant approved General Guide exemplar (structural cue only):\n"
        f"Exemplar question: {exemplar['question']}\n"
        + (f"Recorded theme: {exemplar['known_theme']}\n" if exemplar["known_theme"] else "")
        + ("Relevant quality checks: " + "; ".join(exemplar["assertions"]) + "\n" if exemplar["assertions"] else "")
        + "Apply only the transferable response structure and quality: answer the "
        "actual question directly, make the key distinction or reasoning concrete, "
        "respect the visitor's agency and uncertainty, and use a natural pace. "
        "Rebuild the substance for the current question and its supplied evidence. "
        "Do not copy claims, examples, or any destination from this exemplar unless "
        "independently relevant and supported. The current visitor's explicit "
        "instructions and current Archive evidence take precedence. If the match "
        "is not genuinely relevant, ignore this exemplar.\n\n"
    )
    return guidance, str(exemplar["benchmark_id"])
