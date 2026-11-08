"""Governed structural lessons derived from explicitly approved Gold Stars.

The version-controlled Gold Standard Registry remains authoritative. This module
returns response-shape guidance only: never answer text, facts, citations, or
destination authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONTRACT_VERSION = "v1"
_REGISTRY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"

# Deliberately narrower than the historical feature branch: reconstructed,
# pending, frozen, candidate, and evaluation-only records cannot guide answers.
_ALLOWED_STATUSES = frozenset({"USER_APPROVED_GOLD_STANDARD"})

_STOP_WORDS = frozenset({
    "a","about","after","all","also","an","and","are","as","at","be","because",
    "been","before","but","by","can","could","do","does","for","from","how",
    "i","if","in","into","is","it","its","more","most","not","of","on","or",
    "our","should","so","that","the","their","this","to","what","when","where",
    "which","who","why","with","would","you","your","concept","concepts",
    "difference","differences","explain","important","meaning","question",
    "questions","understand","understanding","way","ways"
})

def _tokens(value: Any) -> set[str]:
    words = re.findall(r"[a-z0-9]+", str(value or "").casefold())
    return {word for word in words if len(word) > 2 and word not in _STOP_WORDS}

def _normalized_phrase(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").casefold()))

def _load_exemplars() -> List[Dict[str, Any]]:
    try:
        payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        records = payload.get("records", [])
    except (OSError, ValueError, TypeError):
        return []
    if not isinstance(records, list):
        return []

    result: List[Dict[str, Any]] = []
    seen_ids = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("subsystem") != "general-purpose-guide":
            continue
        if record.get("status") not in _ALLOWED_STATUSES:
            continue
        benchmark_id = str(record.get("benchmark_id") or "").strip()
        query = str(record.get("query") or "").strip()
        if not benchmark_id or not query or benchmark_id in seen_ids:
            continue
        variants = record.get("related_question_variants") or []
        variant_text = " ".join(str(v) for v in variants if isinstance(v, str))
        terms = _tokens(query + " " + str(record.get("known_theme") or "") + " " + variant_text)
        if not terms:
            continue
        assertions = [str(x).strip() for x in (record.get("assertions") or [])
                      if isinstance(x, str) and str(x).strip()][:3]
        result.append({
            "id": benchmark_id,
            "status": str(record.get("status")),
            "query": query,
            "known_theme": str(record.get("known_theme") or "").strip(),
            "assertions": assertions,
            "terms": terms,
        })
        seen_ids.add(benchmark_id)
    return result

_EXEMPLARS = _load_exemplars()

def select_exemplar(query: str) -> Optional[Dict[str, Any]]:
    """Select one high-confidence structural analogue, otherwise abstain."""
    normalized_query = _normalized_phrase(query)
    if not normalized_query:
        return None

    exact = [x for x in _EXEMPLARS if _normalized_phrase(x["query"]) == normalized_query]
    if len(exact) == 1:
        x = exact[0]
        return {"benchmark_id": x["id"], "score": 1.0, "query": x["query"],
                "known_theme": x["known_theme"], "assertions": x["assertions"]}

    query_terms = _tokens(query)
    if len(query_terms) < 2:
        return None

    ranked = []
    for x in _EXEMPLARS:
        overlap = query_terms & x["terms"]
        if len(overlap) < 2:
            continue
        score = (2.0 * len(overlap)) / (len(query_terms) + len(x["terms"]))
        coverage = len(overlap) / len(query_terms)
        if score >= 0.22 and coverage >= 0.34:
            ranked.append((score, coverage, len(overlap), x["id"], x))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
    score, coverage, overlap_count, _, x = ranked[0]
    if len(ranked) > 1:
        runner = ranked[1]
        if score-runner[0] < 0.035 and overlap_count == runner[2] and abs(coverage-runner[1]) < 0.08:
            return None
    return {"benchmark_id": x["id"], "score": round(score, 3), "query": x["query"],
            "known_theme": x["known_theme"], "assertions": x["assertions"]}

def build_exemplar_guidance(query: str) -> Tuple[str, str]:
    """Return bounded structural guidance and a stable cache token."""
    exemplar = select_exemplar(query)
    if not exemplar:
        return "", "none"
    guidance = (
        "Potentially relevant reviewed Gold Star (structural cue only):\n"
        f"Exemplar question: {exemplar['query']}\n"
        + (f"Recorded theme: {exemplar['known_theme']}\n" if exemplar["known_theme"] else "")
        + ("Relevant quality checks: " + "; ".join(exemplar["assertions"]) + "\n"
           if exemplar["assertions"] else "")
        + "Transfer only genuinely relevant response structure and quality. Rebuild all "
          "substance for the visitor's actual question and current evidence. Do not copy "
          "the exemplar's answer, claims, examples, wording, citations, or destination. "
          "Current evidence and the visitor's instructions take precedence. If the analogy "
          "is not genuinely relevant, ignore it.\n\n"
    )
    return guidance, exemplar["benchmark_id"]
