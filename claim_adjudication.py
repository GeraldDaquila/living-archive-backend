"""Provider-neutral, fail-closed adjudication of answer claims against retrieved passages.

This module owns no provider SDK, network access, retrieval, or visitor logging.
Callers inject bounded claim-extraction and assessment functions. Provider output
is treated as untrusted structured data and cannot establish attribution unless
its exact quoted text occurs in the identified retrieved passage.
"""
from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

VERSION = "1.0"
OUTCOMES = frozenset({
    "supported",
    "partially_supported",
    "contradicted",
    "stale_or_unavailable",
    "no_relevant_public_source",
    "unassessed",
})
_ATTRIBUTED_OUTCOMES = frozenset({"supported", "partially_supported", "contradicted"})
_MAX_CLAIMS = 32
_MAX_PASSAGES = 64
_MAX_PASSAGE_CHARS = 4000
_MAX_QUOTE_CHARS = 1200
_MAX_CLAIM_CHARS = 1200


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _passages(documents: Sequence[Any]) -> list[dict[str, str]]:
    """Create bounded, stable passage identities from the actual retrieved bodies."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, document in enumerate(documents or []):
        if not isinstance(document, Mapping):
            continue
        # Only an explicit trusted caller assertion may cross the visitor boundary.
        # Protected authority material is never implicitly public merely because it
        # was available to generation or internal question selection.
        if document.get("visitor_visible") is not True:
            continue
        access_class = str(document.get("access_class") or "").strip().casefold()
        access_tokens = set(re.split(r"[^a-z0-9]+", access_class))
        protected_flags = (
            "private", "is_private", "protected", "is_protected",
            "steward_only", "guardian_only", "requires_authentication",
            "restricted_access",
        )
        if (
            access_tokens.intersection({"private", "protected", "steward", "guardian", "t4", "restricted"})
            or any(document.get(flag) is True for flag in protected_flags)
        ):
            continue
        title = str(document.get("title") or "").strip()[:300]
        url = str(document.get("url") or "").strip()[:1000]
        source_id = str(document.get("id") or "").strip()[:128]
        body = str(document.get("text") or document.get("content") or document.get("excerpt") or "")
        source_status = str(document.get("source_status") or document.get("availability_status") or document.get("status") or "").strip().casefold()
        if not body.strip():
            continue
        # Paragraph boundaries are retained; no synthetic passage text is created.
        chunks = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
        for chunk_index, chunk in enumerate(chunks):
            chunk = chunk[:_MAX_PASSAGE_CHARS]
            identity = "\n".join((source_id, url, str(index), str(chunk_index), chunk))
            passage_id = _digest(identity)[:24]
            if passage_id in seen:
                continue
            seen.add(passage_id)
            result.append({
                "passage_id": passage_id,
                "source_id": _digest(source_id or url + title)[:24],
                "title": title,
                "url": url,
                "source_status": source_status,
                "text": chunk,
            })
            if len(result) >= _MAX_PASSAGES:
                return result
    return result


def _unassessed(claim: str, reason: str) -> dict[str, Any]:
    return {
        "claim": claim,
        "outcome": "unassessed",
        "reason": reason,
        "attributions": [],
    }


def adjudicate_answer_claims(
    answer: str,
    documents: Sequence[Any],
    *,
    extract_claims: Callable[[str], Any] | None = None,
    assess_claim: Callable[[str, Sequence[Mapping[str, str]]], Any] | None = None,
    adjudicate_claims: Callable[[str, Sequence[Mapping[str, str]]], Any] | None = None,
) -> dict[str, Any]:
    """Extract and adjudicate claims using injected provider-neutral callables.

    ``documents`` must be pre-filtered visitor-visible sources. A document must
    explicitly carry ``visitor_visible=True``; protected, private, Steward,
    Guardian, T4, and restricted material is rejected even if mislabelled visible.
    The callbacks must be bounded by the caller's request deadline. Exceptions,
    missing callbacks, malformed structures, and unverifiable citations never
    become positive or negative findings.
    """
    source_passages = _passages(documents or [])
    if not source_passages:
        return {
            "version": VERSION,
            "status": "no_relevant_public_source",
            "claims": [],
            "claim_count": 0,
        }
    combined_provider = callable(adjudicate_claims)
    if not combined_provider and (not callable(extract_claims) or not callable(assess_claim)):
        return {
            "version": VERSION,
            "status": "unassessed",
            "reason": "adjudication_provider_unavailable",
            "claims": [],
            "claim_count": 0,
        }

    try:
        extracted = (
            adjudicate_claims(str(answer or ""), source_passages)
            if combined_provider
            else extract_claims(str(answer or ""))
        )
    except Exception:
        return {
            "version": VERSION,
            "status": "unassessed",
            "reason": "claim_adjudication_failed" if combined_provider else "claim_extraction_failed",
            "claims": [],
            "claim_count": 0,
        }
    if not isinstance(extracted, list) or not extracted or len(extracted) > _MAX_CLAIMS:
        return {
            "version": VERSION,
            "status": "unassessed",
            "reason": "malformed_claim_extraction",
            "claims": [],
            "claim_count": 0,
        }

    output: list[dict[str, Any]] = []
    passage_index = {item["passage_id"]: item for item in source_passages}
    for item in extracted:
        claim = str(item.get("claim") or "").strip() if isinstance(item, Mapping) else ""
        if not claim or len(claim) > _MAX_CLAIM_CHARS:
            output.append(_unassessed(claim[:_MAX_CLAIM_CHARS], "malformed_claim"))
            continue
        answer_quote = ""
        if combined_provider:
            answer_quote = str(item.get("answer_quote") or "")
            if (
                not answer_quote.strip()
                or len(answer_quote) > _MAX_QUOTE_CHARS
                or answer_quote not in str(answer or "")
            ):
                output.append(_unassessed(claim, "unverifiable_answer_claim"))
                continue
            assessment = item
        else:
            try:
                assessment = assess_claim(claim, source_passages)
            except Exception:
                output.append(_unassessed(claim, "assessment_provider_failed"))
                continue
        if not isinstance(assessment, Mapping):
            output.append(_unassessed(claim, "malformed_assessment"))
            continue
        outcome = str(assessment.get("outcome") or "").strip()
        if outcome not in OUTCOMES or outcome == "unassessed":
            output.append(_unassessed(claim, "invalid_or_unassessed_provider_result"))
            continue

        raw_attributions = assessment.get("attributions")
        if not isinstance(raw_attributions, list):
            output.append(_unassessed(claim, "malformed_attributions"))
            continue
        verified: list[dict[str, str]] = []
        attribution_invalid = False
        for attribution in raw_attributions:
            if not isinstance(attribution, Mapping):
                attribution_invalid = True
                break
            passage_id = str(attribution.get("passage_id") or "").strip()
            quote = str(attribution.get("quote") or "")
            passage = passage_index.get(passage_id)
            if (
                passage is None
                or not quote.strip()
                or len(quote) > _MAX_QUOTE_CHARS
                or quote not in passage["text"]
            ):
                attribution_invalid = True
                break
            verified.append({
                "passage_id": passage_id,
                "source_id": passage["source_id"],
                "title": passage["title"],
                "url": passage["url"],
                "quote": quote,
            })
        if attribution_invalid:
            output.append(_unassessed(claim, "unverifiable_passage_attribution"))
            continue
        if outcome in _ATTRIBUTED_OUTCOMES and not verified:
            output.append(_unassessed(claim, "missing_passage_attribution"))
            continue
        if outcome in {"stale_or_unavailable", "no_relevant_public_source"} and verified:
            output.append(_unassessed(claim, "unexpected_attribution_for_non_evidentiary_outcome"))
            continue
        if outcome == "stale_or_unavailable":
            stale_states = {"stale", "unavailable", "not_found", "removed", "expired", "source_unavailable"}
            if not any(passage.get("source_status") in stale_states for passage in source_passages):
                output.append(_unassessed(claim, "stale_or_unavailable_not_verified_by_source_metadata"))
                continue
            if not str(assessment.get("reason") or "").strip():
                output.append(_unassessed(claim, "missing_stale_or_unavailable_reason"))
                continue
        output_item = {
            "claim": claim,
            "outcome": outcome,
            "reason": str(assessment.get("reason") or "")[:300],
            "attributions": verified,
        }
        if combined_provider:
            output_item["answer_quote"] = answer_quote
        output.append(output_item)

    counts = {outcome: sum(1 for claim in output if claim["outcome"] == outcome) for outcome in sorted(OUTCOMES)}
    overall = "assessed" if output and all(item["outcome"] != "unassessed" for item in output) else "unassessed"
    return {
        "version": VERSION,
        "status": overall,
        "claims": output,
        "claim_count": len(output),
        "outcome_counts": counts,
    }
