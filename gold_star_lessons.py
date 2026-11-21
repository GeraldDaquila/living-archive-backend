"""Governed structural lessons derived from explicitly approved Gold Stars.

Approved Gold Stars contribute reviewed structural discipline to provider-composed
answers and, when explicitly eligible, to deterministic recovery through a
separate bounded adaptation adapter. Registry answers, factual claims, examples,
citations, and doorways are never transferred across questions. Deterministic
eligibility is explicit and never inferred from general adaptive activation.
Exact approved questions retain their separate answer authority.
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
    "questions","understand","understanding","way","ways",
    # Broad decision/context vocabulary cannot establish subject identity by itself.
    "people","person","act","action","actions","acting","future","uncertain",
    "uncertainty","consequential","consequence","consequences","decision",
    "decisions","responsibility","responsibilities","responsible","change",
    "changes","changing","system","systems","outcome","outcomes","impact",
    "impacts","important","significant","matter","matters","options","option"
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
    """Return subject identity, not prose that could make an analogy self-fulfilling.

    Cross-question matching is grounded in the approved question, its known
    theme, reasoning family, and reviewed variants. Transferable discipline,
    qualifying context, and assertions are deliberately excluded: those fields
    describe how a lesson reasons and can contain broad words (e.g. action,
    future, uncertainty) that falsely attract unrelated questions.
    """
    return _concept_terms(" ".join((
        str(lesson.get("query") or ""),
        str(lesson.get("known_theme") or ""),
        str(lesson.get("reasoning_family") or ""),
        " ".join(str(x) for x in lesson.get("variants") or []),
    )))

class GoldStarRegistryIntegrityError(RuntimeError):
    """Raised when the canonical Gold Star ledger violates a hard invariant."""


def validate_learning_integrity(
    records: List[Dict[str, Any]],
    review_entries: List[Dict[str, Any]],
) -> None:
    """Validate learning identity, approvals, and transfer-review integrity only.

    Display serials are intentionally excluded: they are editorial inventory metadata,
    not adaptive-learning identities or eligibility criteria.
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
                # Explicit unknown historical state; recognized for integrity only,
                # never interpreted as an approved omission or a no-match result.
                "NOT_EVALUATED",
            }:
                raise GoldStarRegistryIntegrityError(
                    f"Approved Gold Star {benchmark_id} has no recognized explicit doorway state."
                )
        elif not isinstance(doorway, dict) or not str(doorway.get("title") or "").strip() or not str(doorway.get("url") or "").strip():
            raise GoldStarRegistryIntegrityError(
                f"Approved Gold Star {benchmark_id} has an incomplete expected_doorway."
            )



def validate_numbering_integrity(
    records: List[Dict[str, Any]],
    numbering_gap_register: Optional[List[Dict[str, Any]]],
    numbering_policy: Optional[Dict[str, Any]],
) -> None:
    """Validate display-serial accounting independently from adaptive learning."""
    approved = [
        r for r in records
        if isinstance(r, dict) and r.get("status") in _ALLOWED_STATUSES
    ]
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



def validate_registry_integrity(
    records: List[Dict[str, Any]],
    review_entries: List[Dict[str, Any]],
    numbering_gap_register: Optional[List[Dict[str, Any]]] = None,
    numbering_policy: Optional[Dict[str, Any]] = None,
) -> None:
    """Run both independent validators for full registry/CI integrity checks."""
    validate_learning_integrity(records, review_entries)
    validate_numbering_integrity(records, numbering_gap_register, numbering_policy)


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
    # Runtime learning is keyed by benchmark_id and must remain available even
    # when display-serial bookkeeping is being repaired or independently audited.
    validate_learning_integrity(records, review_entries)
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
            # This is an explicit capability declaration, never inferred from
            # general adaptive-learning activation. Deterministic recovery consumes
            # it only through deterministic_fallback_contribution().
            "deterministic_fallback_eligible": bool(capabilities.get("deterministic_fallback_eligible")),
            "reasoning_family": str(review.get("reasoning_family") or "").strip(),
            "abstention_boundary": str(review.get("abstention_boundary") or "").strip(),
            "qualifying_context": qualifying_context,
            "transferable_discipline": transferable_discipline,
            "variants": [str(v).strip() for v in variants if isinstance(v, str) and str(v).strip()],
        })
        # Precompute matching signatures once at process startup. The
        # selector should not repeatedly tokenize every approved lesson for
        # every visitor request as the registry grows.
        lesson = lessons[-1]
        lesson["signature_terms"] = _lesson_signature(lesson)
        lesson["variant_terms"] = _concept_terms(" ".join(lesson["variants"]))
        lesson["reasoning_terms"] = _concept_terms(lesson["reasoning_family"])
        seen.add(benchmark_id)
    return lessons

_LESSONS = _load_lessons()

def _lesson_candidate_payload(x: Dict[str, Any], score: float, *, exact: bool = False) -> Dict[str, Any]:
    return {
        "benchmark_id": x["id"], "score": round(float(score), 3), "exact": exact,
        "runtime_transfer": bool(x.get("runtime_transfer")),
        "deterministic_fallback_eligible": bool(x.get("deterministic_fallback_eligible")),
        "query": x["query"], "known_theme": x["known_theme"],
        "assertions": x["assertions"],
        "reasoning_family": x.get("reasoning_family", ""),
        "transferable_discipline": x.get("transferable_discipline", ""),
        "abstention_boundary": x.get("abstention_boundary", ""),
    }


def select_lesson_candidates(
    query: str,
    *,
    required_capability: Optional[str] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Preserve proven lexical rankings; use semantic retrieval for missed paraphrases.

    Exact-query authority remains exclusive. The established selector is the
    compatibility baseline: if it finds candidates, its ranking is unchanged.
    BGE retrieval is then used to recover genuinely paraphrased questions that
    the baseline cannot see. Semantic candidates remain guidance-only and are
    subject to model adjudication.
    """
    normalized = _normalized_phrase(query)
    if not normalized or limit < 1:
        return []

    def eligible(item: Dict[str, Any]) -> bool:
        return not required_capability or (
            bool(item.get("runtime_transfer")) and bool(item.get(required_capability))
        )

    exact = [
        x for x in _LESSONS
        if _normalized_phrase(x["query"]) == normalized and eligible(x)
    ]
    if len(exact) == 1:
        return [_lesson_candidate_payload(exact[0], 1.0, exact=True)]

    candidates = [x for x in _LESSONS if x["runtime_transfer"] and eligible(x)]
    query_terms = _tokens(query)
    if len(query_terms) < 2:
        return []

    # Compatibility baseline: preserve the existing, audited lexical selector
    # exactly whenever it has a match. Semantic retrieval is additive recovery,
    # not a replacement that can reorder or erase proven outcomes.
    normalized_query_terms = _concept_terms(query)
    lexical_ranked = []
    for item in candidates:
        shared_signature = normalized_query_terms & item.get("signature_terms", set())
        shared_variant = normalized_query_terms & item.get("variant_terms", set())
        shared_family = normalized_query_terms & item.get("reasoning_terms", set())
        if len(shared_signature) < 2:
            continue
        coverage = len(shared_signature) / max(1, len(normalized_query_terms))
        if coverage < 0.20:
            continue
        score = min(
            0.94,
            0.42 + 0.08 * len(shared_signature)
            + 0.08 * len(shared_family) + 0.04 * len(shared_variant)
            + 0.12 * coverage,
        )
        # Low-confidence lexical resemblance is not enough to transfer a
        # governance lesson into an unrelated visitor domain.
        if score < 0.50:
            continue
        lexical_ranked.append((score, len(shared_signature), item["id"], item))
    lexical_ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    if lexical_ranked:
        return [
            _lesson_candidate_payload(row[3], row[0])
            for row in lexical_ranked[:limit]
        ]

    # Semantic recovery only runs when the proven selector abstains. Missing
    # model/runtime support safely preserves the old abstention behaviour.
    try:
        from gold_star_semantic_retrieval import rank_semantic_lessons
        semantic_scores = rank_semantic_lessons(query, candidates)
    except Exception as exc:
        _TELEMETRY_LOG.warning(
            "gold_star_semantic_retrieval unavailable; preserving legacy abstention: %s",
            type(exc).__name__,
        )
        return []

    ranked = []
    for item in candidates:
        semantic_score = float(semantic_scores.get(item["id"], 0.0))
        shared_signature = normalized_query_terms & item.get("signature_terms", set())
        shared_variant = normalized_query_terms & item.get("variant_terms", set())
        shared_family = normalized_query_terms & item.get("reasoning_terms", set())
        # A subject-identity anchor prevents broad conceptual analogy from
        # crossing domains; semantic similarity supplies the paraphrase bridge.
        if semantic_score < 0.65 or not (shared_signature or shared_variant):
            continue
        lexical_support = min(
            1.0,
            0.18 * len(shared_signature)
            + 0.12 * len(shared_variant)
            + 0.08 * len(shared_family),
        )
        score = min(0.97, 0.78 * semantic_score + 0.22 * lexical_support)
        # Similarity alone must clear a minimum combined relevance floor.
        if score < 0.50:
            continue
        ranked.append((score, semantic_score, len(shared_signature), item["id"], item))

    ranked.sort(key=lambda row: (-row[0], -row[1], -row[2], row[3]))
    if not ranked:
        return []
    if len(ranked) > 1 and ranked[0][0] - ranked[1][0] < 0.025:
        _TELEMETRY_LOG.info(
            "gold_star_semantic_retrieval abstain=ambiguous top=%s second=%s",
            ranked[0][3], ranked[1][3],
        )
        return []
    return [
        _lesson_candidate_payload(row[4], row[0])
        for row in ranked[:limit]
    ]


def select_lesson(
    query: str,
    *,
    required_capability: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Backward-compatible single-best selector; never implies multi-candidate approval."""
    candidates = select_lesson_candidates(
        query, required_capability=required_capability, limit=1
    )
    return candidates[0] if candidates else None

def shadow_observation(
    query: str,
    *,
    request_id: Optional[str] = None,
    request_ledger_version: Optional[str] = None,
) -> Tuple[Optional[str], Optional[float]]:
    """Return minimal non-content metadata and emit a structured shadow event.

    Query text and Gold Star answer content are deliberately excluded from
    telemetry. Opaque request correlation permits joining retrieval to later
    exposure, provider, and delivery stages without retaining visitor content.
    This function remains observation-only and cannot affect composition.
    """
    correlation = ""
    safe_request_id = str(request_id or "").strip()
    if re.fullmatch(r"[0-9a-f]{32}", safe_request_id):
        correlation = " request_id=" + safe_request_id
        version = str(request_ledger_version or "").strip()
        if version:
            correlation += " request_ledger_version=" + version

    selected = select_lesson(query)
    if not selected:
        message = "gold_star_shadow match=abstain" + correlation
        print(message, flush=True)
        _TELEMETRY_LOG.info(message)
        return None, None
    benchmark_id = str(selected["benchmark_id"])
    score = float(selected["score"])
    match_kind = "exact" if bool(selected.get("exact")) else "cross_question"
    message = (
        f"gold_star_shadow match=matched benchmark_id={benchmark_id} "
        f"score={score:.3f} kind={match_kind}" + correlation
    )
    print(message, flush=True)
    _TELEMETRY_LOG.info(message)
    return benchmark_id, score


def active_quality_contribution(query: str) -> Optional[Dict[str, Any]]:
    """Return up to three ranked structural candidates for explicit adjudication."""
    candidates = select_lesson_candidates(query, limit=3)
    if not candidates:
        return None
    primary = candidates[0]
    discipline = str(primary.get("transferable_discipline") or "").strip()
    if not discipline:
        return None
    contribution = {
        "benchmark_id": primary["benchmark_id"],
        "reasoning_family": primary.get("reasoning_family", ""),
        "discipline": discipline,
        "abstention_boundary": primary.get("abstention_boundary", ""),
        "score": float(primary.get("score") or 0.0),
        "exact": bool(primary.get("exact")),
        "authority_mode": "structural_guidance_only",
        "candidates": [
            {
                "benchmark_id": item["benchmark_id"],
                "score": item["score"],
                "exact": item["exact"],
                "query": item["query"],
                "known_theme": item["known_theme"],
                "reasoning_family": item["reasoning_family"],
                "discipline": item["transferable_discipline"],
                "abstention_boundary": item["abstention_boundary"],
            }
            for item in candidates
        ],
    }
    print(
        f"gold_star_quality candidates={len(candidates)} "
        f"top={primary['benchmark_id']} score={primary['score']:.3f}",
        flush=True,
    )
    return contribution

def deterministic_fallback_contribution(query: str) -> Optional[Dict[str, Any]]:
    """Return reviewed guidance only when the Gold Star explicitly permits deterministic use.

    Exact matches are accepted; cross-question analogues require a stronger
    confidence floor. Only structural discipline and its boundary are returned.
    """
    # An exact approved benchmark is an explicit capability boundary. If that
    # exact exemplar is not deterministic-fallback eligible, do not let a looser
    # cross-question analogue override its declared authority.
    exact = [x for x in _LESSONS if _normalized_phrase(x["query"]) == _normalized_phrase(query)]
    if exact:
        if len(exact) != 1 or not exact[0].get("deterministic_fallback_eligible"):
            return None
    selected = select_lesson(query, required_capability="deterministic_fallback_eligible")
    if not selected:
        return None
    score = float(selected.get("score") or 0.0)
    if not selected.get("exact") and score < 0.65:
        return None
    discipline = str(selected.get("transferable_discipline") or "").strip()
    boundary = str(selected.get("abstention_boundary") or "").strip()
    if not discipline or not boundary:
        return None
    return {
        "benchmark_id": str(selected.get("benchmark_id") or ""),
        "score": score,
        "reasoning_family": str(selected.get("reasoning_family") or ""),
        "discipline": discipline,
        "abstention_boundary": boundary,
        "authority_mode": "deterministic_structural_guidance_only",
    }


def apply_deterministic_fallback_guidance(query: str, response: str) -> str:
    """Preserve authored deterministic prose; never paste a lesson into paragraph three.

    Deterministic recoveries are pre-authored answer templates, not generative
    prompts. A Gold Star may inform their design and regression criteria, but
    appending its discipline and abstention text to an existing answer creates
    a fourth cognitive move inside the conclusion and can import an unrelated
    exemplar's subject. Exact Gold Star answers retain their separate registry
    authority; cross-question deterministic guidance is therefore non-mutating.
    """
    return str(response or "").strip()
