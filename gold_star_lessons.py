"""Governed structural lessons derived from explicitly approved Gold Stars.

Approved Gold Stars may actively contribute transferable response discipline to
new answers. Registry answers, factual claims, examples, citations, and doorways
are never transferred across questions; only reviewed structural guidance may
enter composition. Exact approved questions retain their separate answer authority.
"""
from __future__ import annotations

import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONTRACT_VERSION = "v1"
_TELEMETRY_LOG = logging.getLogger("use.gold_star.shadow")
_REGISTRY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
_TRANSFER_REVIEW_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"
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

class GoldStarRegistryIntegrityError(RuntimeError):
    """Raised when the canonical Gold Star ledger violates a hard invariant."""


def validate_registry_integrity(
    records: List[Dict[str, Any]],
    review_entries: List[Dict[str, Any]],
) -> None:
    """Enforce the canonical accounting contract before Gold Stars become active.

    This validator is deliberately fail-closed: an inconsistent approved ledger
    must not silently degrade into partial or ambiguous runtime quality guidance.
    """
    approved = [
        r for r in records
        if isinstance(r, dict)
        and r.get("subsystem") == "general-purpose-guide"
        and r.get("status") in _ALLOWED_STATUSES
    ]
    ids = [str(r.get("benchmark_id") or "").strip() for r in approved]
    if not all(ids):
        raise GoldStarRegistryIntegrityError(
            "Approved Gold Star is missing benchmark_id."
        )
    if len(ids) != len(set(ids)):
        raise GoldStarRegistryIntegrityError(
            "Duplicate approved Gold Star benchmark_id detected."
        )

    review_ids: List[str] = []
    for entry in review_entries:
        if not isinstance(entry, dict):
            raise GoldStarRegistryIntegrityError(
                "Qualitative transfer review contains a non-object entry."
            )
        benchmark_id = str(entry.get("benchmark_id") or "").strip()
        if not benchmark_id:
            raise GoldStarRegistryIntegrityError(
                "Qualitative transfer review is missing benchmark_id."
            )
        review_ids.append(benchmark_id)
        for field in (
            "reasoning_family",
            "transferable_discipline",
            "abstention_boundary",
            "activation",
        ):
            if not str(entry.get(field) or "").strip():
                raise GoldStarRegistryIntegrityError(
                    f"Transfer review {benchmark_id} is missing {field}."
                )
    if len(review_ids) != len(set(review_ids)):
        raise GoldStarRegistryIntegrityError(
            "Duplicate qualitative transfer review benchmark_id detected."
        )
    if set(ids) != set(review_ids):
        missing = sorted(set(ids) - set(review_ids))
        orphaned = sorted(set(review_ids) - set(ids))
        raise GoldStarRegistryIntegrityError(
            f"Gold Star/review reconciliation failed: "
            f"missing_reviews={missing}; orphan_reviews={orphaned}."
        )

    for record in approved:
        benchmark_id = str(record["benchmark_id"]).strip()
        if not str(record.get("query") or "").strip():
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} is missing query."
            )
        if not str(record.get("expected_response") or "").strip():
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} is missing expected_response."
            )
        if not str(record.get("known_theme") or "").strip():
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} is missing known_theme."
            )
        if not isinstance(record.get("runtime_transfer"), bool):
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} must explicitly declare runtime_transfer."
            )
        if not str(record.get("freeze_policy") or "").strip():
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} is missing freeze_policy."
            )
        if "expected_doorway" not in record:
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} is missing explicit expected_doorway state."
            )
        doorway = record.get("expected_doorway")
        if doorway is None:
            doorway_status = str(record.get("doorway_status") or "").strip()
            if doorway_status not in {
                "INTENTIONALLY_NONE_APPROVED",
                "LEGACY_INCOMPLETE_NOT_APPROVED",
            }:
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} has no explicit doorway state."
                )
        elif not isinstance(doorway, dict) or not str(doorway.get("title") or "").strip() or not str(doorway.get("url") or "").strip():
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} has an incomplete expected_doorway."
            )


def _load_transfer_review() -> Dict[str, Dict[str, Any]]:
    """Load qualitative transfer governance keyed by approved benchmark id."""
    try:
        entries = json.loads(_TRANSFER_REVIEW_PATH.read_text(encoding="utf-8")).get("entries", [])
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(entries, list):
        return {}
    review = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        benchmark_id = str(entry.get("benchmark_id") or "").strip()
        if benchmark_id:
            review[benchmark_id] = entry
    return review

def _load_lessons() -> List[Dict[str, Any]]:
    try:
        registry_payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        review_payload = json.loads(_TRANSFER_REVIEW_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise GoldStarRegistryIntegrityError(
            "Canonical Gold Star registry or qualitative review cannot be read."
        ) from exc
    records = registry_payload.get("records", [])
    review_entries = review_payload.get("entries", [])
    if not isinstance(records, list) or not isinstance(review_entries, list):
        raise GoldStarRegistryIntegrityError(
            "Canonical Gold Star registry or qualitative review has an invalid top-level schema."
        )
    validate_registry_integrity(records, review_entries)
    transfer_review = {
        str(entry.get("benchmark_id") or "").strip(): entry
        for entry in review_entries
        if isinstance(entry, dict) and str(entry.get("benchmark_id") or "").strip()
    }
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
        review = transfer_review.get(benchmark_id, {})
        capabilities = record.get("gold_star_capabilities") or {}
        active_candidate = bool(capabilities.get("active_quality_contributor")) or review.get("activation") in {"active_quality_contributor", "shadow_candidate"}
        qualifying_context = str(review.get("qualifying_context") or "")
        transferable_discipline = str(review.get("transferable_discipline") or "")
        lessons.append({
            "id": benchmark_id,
            "query": query,
            "known_theme": str(record.get("known_theme") or "").strip(),
            "assertions": assertions,
            "terms": _tokens(query + " " + str(record.get("known_theme") or "")
                             + " " + " ".join(str(v) for v in variants if isinstance(v, str))),
            # Cross-question eligibility is governed by the qualitative review.
            "runtime_transfer": bool(record.get("runtime_transfer")) or active_candidate,
            "deterministic_fallback_eligible": bool(capabilities.get("deterministic_fallback_eligible")) or active_candidate,
            "reasoning_family": str(review.get("reasoning_family") or "").strip(),
            "abstention_boundary": str(review.get("abstention_boundary") or "").strip(),
            "qualifying_context": qualifying_context,
            "transferable_discipline": transferable_discipline,
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
                "assertions": x["assertions"],
                "reasoning_family": x.get("reasoning_family", ""),
                "transferable_discipline": x.get("transferable_discipline", ""),
                "abstention_boundary": x.get("abstention_boundary", "")}
    candidates = [x for x in _LESSONS if x["runtime_transfer"]]
    query_terms = _tokens(query)
    if len(query_terms) < 2:
        return None
    ranked = []
    for x in candidates:
        variant_terms = set().union(*(_tokens(v) for v in x["variants"])) if x["variants"] else set()
        context_terms = _tokens(x.get("qualifying_context", "") + " " + x.get("transferable_discipline", ""))
        exemplar_terms = _tokens(x["query"]) | context_terms
        shared_exemplar = query_terms & exemplar_terms
        shared_variant = query_terms & variant_terms
        shared_context = query_terms & context_terms
        support = len(shared_variant) + len(shared_context)
        if len(shared_exemplar) < 1 or support < 2:
            continue
        coverage = support / max(1, len(query_terms))
        if coverage < 0.34:
            continue
        score = min(0.99, 0.45 + 0.1 * len(shared_exemplar) + 0.06 * support)
        ranked.append((score, support, x["id"], x))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    score, _, _, x = ranked[0]
    return {"benchmark_id": x["id"], "score": round(score, 3), "exact": False,
            "runtime_transfer": True, "query": x["query"],
            "known_theme": x["known_theme"], "assertions": x["assertions"],
            "reasoning_family": x.get("reasoning_family", ""),
            "transferable_discipline": x.get("transferable_discipline", ""),
            "abstention_boundary": x.get("abstention_boundary", "")}

def shadow_observation(query: str) -> Tuple[Optional[str], Optional[float]]:
    """Return minimal non-content metadata and emit a structured shadow event.

    Query text and Gold Star answer content are deliberately excluded from
    telemetry. This function remains observation-only and cannot affect
    visitor-facing composition.
    """
    selected = select_lesson(query)
    if not selected:
        message = "gold_star_shadow match=abstain"
        print(message, flush=True)
        _TELEMETRY_LOG.info(message)
        return None, None
    benchmark_id = str(selected["benchmark_id"])
    score = float(selected["score"])
    match_kind = "exact" if bool(selected.get("exact")) else "cross_question"
    message = (
        f"gold_star_shadow match=matched benchmark_id={benchmark_id} "
        f"score={score:.3f} kind={match_kind}"
    )
    print(message, flush=True)
    _TELEMETRY_LOG.info(message)
    return benchmark_id, score


def active_quality_contribution(query: str) -> Optional[Dict[str, Any]]:
    """Return bounded structural guidance for real-time composition."""
    selected = select_lesson(query)
    if not selected or not selected.get("runtime_transfer"):
        return None
    discipline = str(selected.get("transferable_discipline") or "").strip()
    if not discipline:
        return None
    contribution = {"benchmark_id": str(selected.get("benchmark_id") or ""), "reasoning_family": str(selected.get("reasoning_family") or ""), "discipline": discipline, "abstention_boundary": str(selected.get("abstention_boundary") or ""), "score": float(selected.get("score") or 0.0), "exact": bool(selected.get("exact")), "authority_mode": "structural_guidance_only"}
    print(f"gold_star_quality active benchmark_id={contribution['benchmark_id']} score={contribution['score']:.3f}", flush=True)
    return contribution
