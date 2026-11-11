"""Governed structural lessons derived from explicitly approved Gold Stars.

This is a shadow-mode quality layer. It selects transferable response structure
without changing visitor-facing composition. Registry answers, claims, examples,
citations, and doorways are never returned as lesson content.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONTRACT_VERSION = "v1"
_REGISTRY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
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
    return {w for w in re.findall(r"[a-z0-9]+", str(value or "").casefold())
            if len(w) > 2 and w not in _STOP_WORDS}

def _normalized_phrase(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").casefold()))

def _load_lessons() -> List[Dict[str, Any]]:
    try:
        records = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8")).get("records", [])
    except (OSError, ValueError, TypeError):
        return []
    if not isinstance(records, list):
        return []
    lessons, seen = [], set()
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("subsystem") != "general-purpose-guide":
            continue
        if record.get("status") not in _ALLOWED_STATUSES:
            continue
        benchmark_id = str(record.get("benchmark_id") or "").strip()
        query = str(record.get("query") or "").strip()
        if not benchmark_id or not query or benchmark_id in seen:
            continue
        variants = record.get("related_question_variants") or []
        if not isinstance(variants, list):
            variants = []
        assertions = [str(x).strip() for x in (record.get("assertions") or [])
                      if isinstance(x, str) and str(x).strip()][:5]
        lessons.append({
            "id": benchmark_id,
            "query": query,
            "known_theme": str(record.get("known_theme") or "").strip(),
            "assertions": assertions,
            "terms": _tokens(query + " " + str(record.get("known_theme") or "")
                             + " " + " ".join(str(v) for v in variants if isinstance(v, str))),
            "runtime_transfer": bool(record.get("runtime_transfer")),
            "variants": [str(v).strip() for v in variants if isinstance(v, str) and str(v).strip()],
        })
        seen.add(benchmark_id)
    return lessons

_LESSONS = _load_lessons()

def select_lesson(query: str) -> Optional[Dict[str, Any]]:
    """Select one explicitly transferable structural analogue, else abstain."""
    normalized = _normalized_phrase(query)
    if not normalized:
        return None
    exact = [x for x in _LESSONS if _normalized_phrase(x["query"]) == normalized]
    if len(exact) == 1:
        x = exact[0]
        return {"benchmark_id": x["id"], "score": 1.0, "exact": True,
                "runtime_transfer": bool(x["runtime_transfer"]),
                "query": x["query"], "known_theme": x["known_theme"],
                "assertions": x["assertions"]}
    candidates = [x for x in _LESSONS if x["runtime_transfer"]]
    query_terms = _tokens(query)
    if len(query_terms) < 2:
        return None
    ranked = []
    for x in candidates:
        variant_terms = set().union(*(_tokens(v) for v in x["variants"])) if x["variants"] else set()
        exemplar_terms = _tokens(x["query"])
        shared_exemplar = query_terms & exemplar_terms
        shared_variant = query_terms & variant_terms
        if len(shared_exemplar) < 1 or len(shared_variant) < 2:
            continue
        coverage = len(shared_variant) / max(1, len(query_terms))
        if coverage < 0.34:
            continue
        score = min(0.99, 0.45 + 0.1 * len(shared_exemplar) + 0.08 * len(shared_variant))
        ranked.append((score, len(shared_variant), x["id"], x))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    score, _, _, x = ranked[0]
    return {"benchmark_id": x["id"], "score": round(score, 3), "exact": False,
            "runtime_transfer": True, "query": x["query"],
            "known_theme": x["known_theme"], "assertions": x["assertions"]}

def shadow_observation(query: str) -> Tuple[Optional[str], Optional[float]]:
    """Return minimal non-content metadata for shadow evaluation and telemetry."""
    selected = select_lesson(query)
    if not selected:
        return None, None
    return selected["benchmark_id"], float(selected["score"])
