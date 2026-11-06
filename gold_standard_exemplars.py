""""Governed, low-cost structural exemplars for the public General Guide.

The version-controlled Gold Standard Registry remains authoritative. Exemplars
supply response-shape guidance only: they never provide answer text, factual
claims, citations, or destination authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONTRACT_VERSION = "v2"
_REGISTRY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"

# Only reviewed reference/approval states may guide live composition. Evaluation
# fixtures, recovered historical candidates, and diagnostic records are excluded.
_ALLOWED_STATUSES = frozenset({
    "USER_APPROVED_GOLD_STANDARD",
    "USER_APPROVED_GOLD_STANDARD_PENDING_FIXTURE",
    "FROZEN_REFERENCE_ONLY",
    "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT",
})

_STOP_WORDS = frozenset({
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "could", "did", "do",
    "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "itself", "just", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "now", "of", "off", "on", "once", "one", "only", "or",
    "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "would", "you", "your", "yours", "yourself", "yourselves",
    # Common framing words are not reliable evidence of a shared subject.
    "among", "concept", "concepts", "differ", "difference", "differences",
    "explain", "explaining", "important", "importance", "matter", "matters",
    "meaning", "mean", "means", "question", "questions", "really", "relation",
    "relationship", "relationships", "role", "roles", "understand",
    "understanding", "way", "ways",
})


def _tokens(value: Any) -> set[str]:
    words = re.findall(r"[a-z0-9]+", str(value or "").casefold())
    return {word for word in words if len(word) > 2 and word not in _STOP_WORDS}


def _normalized_phrase(value: Any) -> str:
    """Normalize punctuation and spacing for exact registry-question identity."""
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").casefold()))


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
        # A missing/malformed optional registry must not prevent Guide startup.
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
        query = str(record.get("query") or "").strip()
        response = _response_for_record(record)
        if not query or not response:
            continue
        benchmark_id = str(record.get("benchmark_id") or "").strip()
        if not benchmark_id or benchmark_id in seen_ids:
            continue
        variants = record.get("related_question_variants") or []
        if not isinstance(variants, list):
            variants = []
        variant_text = " ".join(str(item) for item in variants if isinstance(item, str))
        terms = _tokens(query + " " + str(record.get("known_theme") or "") + " " + variant_text)
        if len(terms) < 2:
            continue
        assertions = record.get("assertions") or []
        structural_assertions = [
            str(item).strip() for item in assertions
            if isinstance(item, str) and str(item).strip()
        ][:3]
        result.append({
            "id": benchmark_id,
            "status": str(record.get("status") or ""),
            "query": query,
            "known_theme": str(record.get("known_theme") or "").strip(),
            "assertions": structural_assertions,
            "terms": terms,
        })
        seen_ids.add(benchmark_id)
    return result


# Load once at process startup. No per-turn registry I/O, network, embedding, or
# model call is introduced by exemplar selection.
_EXEMPLARS = _load_exemplars()


def select_exemplar(query: str) -> Optional[Dict[str, Any]]:
    """Select one high-confidence structural analogue; abstain on weak/ambiguous matches."""
    normalized_query = _normalized_phrase(query)
    if not normalized_query:
        return None

    # Exact registry-question identity is sufficient evidence even when the
    # question contains only one informative subject term (for example,
    # "What does accountability really mean?"). This remains structural
    # guidance only; it never enforces or reconstructs the approved answer.
    exact_matches = [
        exemplar for exemplar in _EXEMPLARS
        if _normalized_phrase(exemplar["query"]) == normalized_query
    ]
    if len(exact_matches) == 1:
        exemplar = exact_matches[0]
        return {
            "benchmark_id": exemplar["id"],
            "status": exemplar["status"],
            "score": 1.0,
            "query": exemplar["query"],
            "known_theme": exemplar["known_theme"],
            "assertions": exemplar["assertions"],
        }
    if len(exact_matches) > 1:
        # Duplicate exact questions with different registry identities are
        # ambiguous; never let file order choose the guidance record.
        return None

    query_terms = _tokens(query)
    if len(query_terms) < 2:
        return None

    ranked: List[Tuple[float, float, int, str, Dict[str, Any]]] = []
    for exemplar in _EXEMPLARS:
        overlap = query_terms & exemplar["terms"]
        overlap_count = len(overlap)
        if overlap_count < 2:
            continue
        score = (2.0 * overlap_count) / (len(query_terms) + len(exemplar["terms"]))
        coverage = overlap_count / len(query_terms)
        # A high Dice score alone can be misleading for a long query that shares
        # only two generic words. Require meaningful coverage of the visitor's
        # actual subject terms as well.
        if score < 0.22 or coverage < 0.34:
            continue
        ranked.append((score, coverage, overlap_count, exemplar["id"], exemplar))

    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
    score, coverage, overlap_count, _, exemplar = ranked[0]

    # Do not let registry order decide between near-equal candidates. An
    # ambiguous question receives no exemplar rather than an arbitrary cue.
    if len(ranked) > 1:
        runner_up = ranked[1]
        if (
            score - runner_up[0] < 0.035
            and overlap_count == runner_up[2]
            and abs(coverage - runner_up[1]) < 0.08
        ):
            return None

    return {
        "benchmark_id": exemplar["id"],
        "status": exemplar["status"],
        "score": round(score, 3),
        "query": exemplar["query"],
        "known_theme": exemplar["known_theme"],
        "assertions": exemplar["assertions"],
    }


def build_exemplar_guidance(query: str) -> Tuple[str, str]:
    """Return bounded structural guidance and a cache-key token."""
    exemplar = select_exemplar(query)
    if not exemplar:
        return "", "none"
    guidance = (
        "Potentially relevant reviewed General Guide exemplar (structural cue only):\n"
        f"Exemplar question: {exemplar['query']}\n"
        + (f"Recorded theme: {exemplar['known_theme']}\n" if exemplar["known_theme"] else "")
        + ("Relevant quality checks: " + "; ".join(exemplar["assertions"]) + "\n" if exemplar["assertions"] else "")
        + "Transfer only the response structure and quality that genuinely fit this "
        "question. Rebuild all substance for the visitor's actual question and the "
        "currently supplied evidence. Do not copy the exemplar's answer, claims, "
        "examples, wording, citations, or destination. Do not force its paragraph "
        "count or response shape when the current question calls for something else. "
        "The visitor's explicit instructions and current evidence take precedence. "
        "If the analogy is not genuinely relevant, ignore it.\n\n"
    )
    return guidance, exemplar["benchmark_id"]
