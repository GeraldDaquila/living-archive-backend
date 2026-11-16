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


def _concept_terms(value: Any) -> set[str]:
    """Normalize structural vocabulary without introducing an external ontology.

    The adaptive layer learns only from reviewer-approved Archive metadata. A
    light stem lets related surface forms meet (orientation/orienting) while
    avoiding speculative synonym expansion.
    """
    terms = _tokens(value)
    normalized = set()
    for term in terms:
        stem = term
        for suffix in ("ations", "ation", "ments", "ment", "ities", "ity", "ing", "ers", "er", "ed", "es", "s"):
            if len(stem) > len(suffix) + 3 and stem.endswith(suffix):
                stem = stem[:-len(suffix)]
                break
        normalized.add(stem)
    return normalized


def _lesson_signature(lesson: Dict[str, Any]) -> set[str]:
    """Return the approved structural vocabulary eligible for analogue matching."""
    return _concept_terms(" ".join((
        str(lesson.get("query") or ""),
        str(lesson.get("known_theme") or ""),
        str(lesson.get("reasoning_family") or ""),
        str(lesson.get("qualifying_context") or ""),
        str(lesson.get("transferable_discipline") or ""),
        " ".join(str(x) for x in lesson.get("variants") or []),
        " ".join(str(x) for x in lesson.get("assertions") or []),
    )))

class GoldStarRegistryIntegrityError(RuntimeError):
    """Raised when the canonical Gold Star ledger violates a hard invariant."""


def validate_registry_integrity(
    records: List[Dict[str, Any]],
    review_entries: List[Dict[str, Any]],
    numbering_gap_register: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Enforce the canonical accounting contract before Gold Stars become active.

    This validator is deliberately fail-closed: an inconsistent approved ledger
    must not silently degrade into partial or ambiguous runtime quality guidance.
    """
    # The Constitution defines one approved inventory by status, not by
    # subsystem label. Subsystem names are descriptive metadata and must not
    # silently exclude an approved contributor from runtime governance.
    approved = [
        r for r in records
        if isinstance(r, dict) and r.get("status") in _ALLOWED_STATUSES
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
    # Only explicitly approved, runtime-active Gold Stars participate in the
    # qualitative transfer contract. Historical registry records remain auditable
    # without requiring a transfer review for every legacy benchmark.
    approved_ids = {
        str(record.get("benchmark_id") or "").strip()
        for record in records
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and bool(record.get("runtime_transfer"))
    }
    if approved_ids != set(review_ids):
        missing = sorted(approved_ids - set(review_ids))
        orphaned = sorted(set(review_ids) - approved_ids)
        raise GoldStarRegistryIntegrityError(
            f"Gold Star/review reconciliation failed: "
            f"missing_reviews={missing}; orphan_reviews={orphaned}."
        )

    # Display serials are not learning identities. Every approved record must
    # declare whether it has one, and unassigned records must explain why.
    # Adaptive selection remains keyed exclusively by benchmark_id.
    assigned_numbers = []
    for record in approved:
        benchmark_id = str(record.get("benchmark_id") or "<missing-id>").strip()
        number = record.get("gold_star_number")
        state = record.get("numbering_status")
        if number is None:
            if state != "UNASSIGNED":
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} lacks explicit UNASSIGNED numbering state."
                )
            if not str(record.get("numbering_unassigned_reason_code") or "").strip() or not str(record.get("numbering_unassigned_reason") or "").strip():
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} lacks its unassigned numbering reason."
                )
        else:
            if isinstance(number, bool) or not isinstance(number, int) or number <= 0 or state != "ASSIGNED":
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} has invalid assigned-number metadata."
                )
            if record.get("numbering_unassigned_reason_code") or record.get("numbering_unassigned_reason"):
                raise GoldStarRegistryIntegrityError(
                    f"Assigned Gold Star {benchmark_id} also carries an unassigned reason."
                )
            recovery = record.get("numbering_recovery")
            if recovery is not None:
                required_recovery = (
                    "recovery_class", "recovered_number", "source_pr", "source_pr_url",
                    "source_merge_commit", "previous_registry_state", "authority_basis",
                    "recovered_at",
                )
                if (
                    not isinstance(recovery, dict)
                    or any(not str(recovery.get(key) or "").strip() for key in required_recovery)
                    or recovery.get("recovered_number") != number
                    or recovery.get("recovery_class") not in {
                        "HISTORICAL_SEQUENCE_ASSIGNMENT_RECOVERY",
                        "HISTORICAL_EXPLICIT_ASSIGNMENT_RECOVERY",
                    }
                    or isinstance(recovery.get("source_pr"), bool)
                    or not isinstance(recovery.get("source_pr"), int)
                ):
                    raise GoldStarRegistryIntegrityError(
                        f"Approved Gold Star {benchmark_id} has incomplete historical numbering recovery evidence."
                    )
            assigned_numbers.append(number)

    if numbering_gap_register is None or not isinstance(numbering_gap_register, list):
        raise GoldStarRegistryIntegrityError(
            "Canonical Gold Star registry is missing numbering_gap_register."
        )
    if not assigned_numbers:
        raise GoldStarRegistryIntegrityError("No assigned Gold Star serials exist.")
    sequence_start = numbering_policy.get("sequence_start") if isinstance(numbering_policy, dict) else None
    if isinstance(sequence_start, bool) or not isinstance(sequence_start, int) or sequence_start <= 0 or min(assigned_numbers) != sequence_start:
        raise GoldStarRegistryIntegrityError("Gold Star numbering_policy.sequence_start does not match the lowest assigned serial.")
    expected_gaps = set(range(sequence_start, max(assigned_numbers) + 1)) - set(assigned_numbers)
    actual_gaps = set()
    for gap in numbering_gap_register:
        if not isinstance(gap, dict):
            raise GoldStarRegistryIntegrityError("Gold Star numbering gap entry is not an object.")
        number = gap.get("number")
        if (
            isinstance(number, bool) or not isinstance(number, int) or number <= 0
            or gap.get("status") != "UNASSIGNED_HISTORICAL_GAP"
            or not str(gap.get("reason_code") or "").strip()
            or not str(gap.get("reason") or "").strip()
            or not isinstance(gap.get("evidence_checked"), list) or not gap.get("evidence_checked")
            or not str(gap.get("disposition") or "").strip()
        ):
            raise GoldStarRegistryIntegrityError("Gold Star numbering gap entry is incomplete.")
        actual_gaps.add(number)
    if len(actual_gaps) != len(numbering_gap_register) or actual_gaps != expected_gaps:
        raise GoldStarRegistryIntegrityError(
            f"Gold Star numbering gaps do not reconcile: expected={sorted(expected_gaps)} actual={sorted(actual_gaps)}."
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
        legacy = record.get("legacy_approval_grandfathered") is True
        if not legacy:
            if record.get("user_reviewed_response") is not True:
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} lacks evidence that the user reviewed the actual response."
                )
            if record.get("explicit_user_elevation_approval") is not True:
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} lacks explicit user authorization for elevation."
                )
            if not str(record.get("elevation_approval_evidence") or "").strip():
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} lacks recorded elevation approval evidence."
                )
        elif not str(record.get("legacy_approval_grandfathered_reason") or "").strip():
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} has an undocumented legacy approval exemption."
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
                "NOT_APPROVED_CONCEPTUAL_MISMATCH",
                "TITLE_OBSERVED_URL_NOT_CAPTURED",
            }:
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} has no recognized explicit doorway state."
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
    validate_registry_integrity(records, review_entries, registry_payload.get("numbering_gap_register"), registry_payload.get("numbering_policy"))
    transfer_review = {
        str(entry.get("benchmark_id") or "").strip(): entry
        for entry in review_entries
        if isinstance(entry, dict) and str(entry.get("benchmark_id") or "").strip()
    }
    lessons, seen = [], set()
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("status") not in _ALLOWED_STATUSES:
            continue
        # All explicitly approved Gold Stars belong to the one constitutional
        # inventory. Relevance and abstention rules, not subsystem labels,
        # govern whether a lesson contributes to a particular visitor question.
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
        # Match against the full reviewer-approved structural signature rather
        # than only the exemplar wording. This lets the system recognize a shared
        # reasoning family expressed in different visitor language while keeping
        # all vocabulary inside the approved Gold Star record and transfer review.
        signature_terms = _lesson_signature(x)
        normalized_query_terms = _concept_terms(query)
        shared_signature = normalized_query_terms & signature_terms
        shared_variant = _concept_terms(" ".join(x["variants"])) & normalized_query_terms
        reasoning_terms = _concept_terms(x.get("reasoning_family", ""))
        shared_family = normalized_query_terms & reasoning_terms
        if len(shared_signature) < 2:
            continue
        coverage = len(shared_signature) / max(1, len(normalized_query_terms))
        if coverage < 0.20:
            continue
        # Reasoning-family overlap is a stronger signal than incidental topic
        # overlap; variants provide a modest bonus. Keep the score below exact
        # authority and abstain rather than forcing weak analogues.
        score = min(
            0.94,
            0.42
            + 0.08 * len(shared_signature)
            + 0.08 * len(shared_family)
            + 0.04 * len(shared_variant)
            + 0.12 * coverage,
        )
        ranked.append((score, len(shared_signature), x["id"], x))
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
