"""Evidence provenance and bounded support signals for Gold Star v2.

This module validates source identity and provenance. It deliberately does not
claim that lexical overlap proves a claim is entailed by a source.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlsplit
from typing import Any, Dict, Iterable, Mapping

VERSION = "1.0"
_ALLOWED_HOSTS = {"geralddaquila.com", "www.geralddaquila.com"}
_ARCHIVE_BASES = {"archive_supported", "archive_reference"}
_TEMPORAL_CUES = re.compile(r"\b(?:today|currently|current|latest|recent|right now|as of|this week|this month|202[6-9])\b", re.I)


def _canonical_https_url(value: Any) -> bool:
    try:
        parsed = urlsplit(str(value or "").strip())
        return (
            parsed.scheme.casefold() == "https"
            and (parsed.hostname or "").casefold() in _ALLOWED_HOSTS
            and not parsed.username
            and not parsed.password
            and parsed.port in (None, 443)
        )
    except Exception:
        return False


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_evidence_assessment(
    query: str,
    answer: str,
    answer_basis: Any,
    documents: Iterable[Any],
    *,
    approved_reference_id: str = "",
    exact_standard: bool = False,
) -> tuple[list[Dict[str, Any]], Dict[str, Any]]:
    """Build visitor-safe evidence references plus conservative validation metadata."""
    basis = answer_basis if isinstance(answer_basis, Mapping) else {}
    kind = str(basis.get("kind") or "").strip()
    if exact_standard:
        return [], {
            "version": VERSION, "status": "not_applicable",
            "reason": "exact_standard_registry_authority",
            "claim_support": {"status": "not_applicable", "semantic_certification": False},
            "temporal_validity": {"status": "not_applicable"},
            "semantic_certification": False,
        }
    if kind not in _ARCHIVE_BASES:
        return [], {
            "version": VERSION, "status": "not_applicable",
            "reason": "answer_not_attributed_to_archive",
            "claim_support": {"status": "not_applicable", "semantic_certification": False},
            "temporal_validity": {"status": "not_applicable"},
            "semantic_certification": False,
        }

    references: list[Dict[str, Any]] = []
    seen_urls: set[str] = set()
    invalid_candidates = 0
    for document in documents or []:
        if not isinstance(document, Mapping):
            invalid_candidates += 1
            continue
        title = str(document.get("title") or "").strip()
        url = str(document.get("url") or "").strip()
        body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").strip()
        if not title or not body or not _canonical_https_url(url):
            invalid_candidates += 1
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        digest = _digest(body)
        references.append({
            "id": _digest(url + "\n" + digest)[:24],
            "title": title[:300],
            "url": url,
            "source_type": "canonical_archive",
            "content_sha256": digest,
            "content_chars": len(body),
            "verification": "canonical_https_url_and_nonempty_source_body",
        })
        if len(references) >= 8:
            break

    if kind == "archive_reference" and approved_reference_id:
        reference_id = str(approved_reference_id).strip()
        if reference_id and not any(item.get("reference_id") == reference_id for item in references):
            references.append({
                "id": "approved-reference:" + _digest(reference_id)[:20],
                "title": "Approved Living Archive reference",
                "source_type": "approved_reference_contract",
                "reference_id": reference_id,
                "verification": "registered_approved_reference_contract",
            })

    if not references:
        return [], {
            "version": VERSION,
            "status": "fail",
            "reason": "archive_claim_without_verified_evidence",
            "invalid_candidates_omitted": invalid_candidates,
            "claim_support": {
                "status": "review_required",
                "reason": "no_verified_source_body",
                "semantic_certification": False,
            },
            "temporal_validity": {
                "status": "review_required" if _TEMPORAL_CUES.search(str(query or "")) else "not_applicable",
                "reason": "retrieval_timestamp_not_available",
            },
            "semantic_certification": False,
        }

    temporal = bool(_TEMPORAL_CUES.search(str(query or "")))
    return references, {
        "version": VERSION,
        "status": "pass",
        "reason": "source_provenance_verified_claim_support_not_certified",
        "reference_count": len(references),
        "invalid_candidates_omitted": invalid_candidates,
        "claim_support": {
            "status": "review_required",
            "reason": "semantic_entailment_requires_task_specific_or_human_review",
            "semantic_certification": False,
        },
        "temporal_validity": {
            "status": "review_required" if temporal else "not_assessed",
            "reason": "retrieval_timestamp_not_available" if temporal else "no_temporal_requirement_detected",
        },
        "semantic_certification": False,
    }


def validate_evidence_payload(
    query: str,
    payload: Any,
    *,
    exact_standard: bool = False,
) -> Dict[str, Any]:
    """Validate evidence identity/provenance without treating similarity as entailment."""
    if not isinstance(payload, Mapping):
        return {"version": VERSION, "status": "not_applicable", "reason": "non_object_payload"}
    if exact_standard:
        return {"version": VERSION, "status": "not_applicable", "reason": "exact_standard_registry_authority"}
    basis = payload.get("answer_basis")
    kind = str(basis.get("kind") or "").strip() if isinstance(basis, Mapping) else ""
    if kind not in _ARCHIVE_BASES:
        return {"version": VERSION, "status": "not_applicable", "reason": "answer_not_attributed_to_archive"}

    references = payload.get("evidence")
    assessment = payload.get("evidence_validation")
    if not isinstance(references, list) or not references:
        return {"version": VERSION, "status": "fail", "reason": "archive_claim_without_verified_evidence"}
    if not isinstance(assessment, Mapping) or assessment.get("status") != "pass":
        return {"version": VERSION, "status": "fail", "reason": "evidence_assessment_missing_or_failed"}

    for reference in references:
        if not isinstance(reference, Mapping) or not str(reference.get("id") or "").strip() or not str(reference.get("title") or "").strip():
            return {"version": VERSION, "status": "fail", "reason": "invalid_evidence_reference"}
        source_type = str(reference.get("source_type") or "")
        if source_type == "canonical_archive":
            try:
                content_chars = int(reference.get("content_chars") or 0)
            except (TypeError, ValueError):
                content_chars = 0
            if (
                not _canonical_https_url(reference.get("url"))
                or not re.fullmatch(r"[0-9a-f]{64}", str(reference.get("content_sha256") or ""))
                or content_chars <= 0
            ):
                return {"version": VERSION, "status": "fail", "reason": "invalid_evidence_reference"}
        elif source_type == "approved_reference_contract":
            if not str(reference.get("reference_id") or "").strip():
                return {"version": VERSION, "status": "fail", "reason": "invalid_approved_reference"}
        else:
            return {"version": VERSION, "status": "fail", "reason": "unknown_evidence_source_type"}

    try:
        declared_reference_count = int(assessment.get("reference_count") or 0)
    except (TypeError, ValueError):
        declared_reference_count = -1
    if declared_reference_count != len(references):
        return {"version": VERSION, "status": "fail", "reason": "evidence_reference_count_mismatch"}
    claim_support = assessment.get("claim_support")
    if not isinstance(claim_support, Mapping) or claim_support.get("semantic_certification") is not False:
        return {"version": VERSION, "status": "fail", "reason": "evidence_claim_support_overstated"}
    return {
        "version": VERSION,
        "status": "pass",
        "reason": "evidence_provenance_valid_claim_support_not_certified",
        "reference_count": len(references),
        "claim_support": dict(claim_support),
        "temporal_validity": dict(assessment.get("temporal_validity") or {}),
        "semantic_certification": False,
    }
