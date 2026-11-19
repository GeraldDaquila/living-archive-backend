"""Shared evidence-source identity and completeness contract.

This module separates source verification from question-specific reasoning.
It validates source identity and usable body presence without requiring brittle
exact-phrase markers or treating a bounded retrieval miss as corpus absence.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

VERSION = "1.0"
DEFAULT_MIN_BODY_CHARS = 250


def normalize_source_url(value: Any) -> str:
    """Normalize a canonical URL for identity comparison, not navigation."""
    raw = str(value or "").strip()
    try:
        parsed = urlsplit(raw)
        if parsed.scheme.casefold() != "https" or not parsed.hostname:
            return ""
        if parsed.username or parsed.password:
            return ""
        if parsed.port not in (None, 443):
            return ""
        host = parsed.hostname.casefold()
        if host.startswith("www."):
            host = host[4:]
        path = re.sub(r"/+", "/", parsed.path or "/").rstrip("/")
        return urlunsplit(("https", host, path, "", ""))
    except Exception:
        return ""


def _title_key(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").casefold()))


def _body_text(document: dict[str, Any]) -> str:
    for key in ("text", "content", "body"):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            return re.sub(r"\s+", " ", value).strip()
    return ""


def verify_retrieved_source_document(
    document: Any,
    *,
    min_body_chars: int = 80,
) -> dict[str, Any]:
    """Verify the minimum identity/body contract for any retrieved source.

    This shared gate is used by canonical WordPress retrieval paths across
    question families. It does not certify relevance or factual correctness;
    those remain the responsibility of the question-fit and reasoning layers.
    """
    if not isinstance(document, dict):
        return {"verified": False, "reason": "invalid_record"}
    title = str(document.get("title") or "").strip()
    url = str(document.get("url") or document.get("canonical_url") or "").strip()
    normalized_url = normalize_source_url(url)
    body = _body_text(document)
    if not title or not normalized_url:
        return {"verified": False, "reason": "source_identity_missing"}
    if len(body) < max(1, int(min_body_chars)):
        return {"verified": False, "reason": "source_body_too_short"}
    return {
        "verified": True,
        "reason": "retrieved_source_identity_and_body_verified",
        "document": {
            **document,
            "title": title,
            "url": url,
            "text": body,
            "source_evidence_contract": VERSION,
            "source_provenance": "retrieved_canonical_body",
        },
    }


def verify_source_document(
    expected: dict[str, Any],
    document: Any,
    *,
    min_body_chars: int = DEFAULT_MIN_BODY_CHARS,
) -> dict[str, Any]:
    """Verify one fetched body against an expected canonical source identity."""
    if not isinstance(expected, dict) or not isinstance(document, dict):
        return {"verified": False, "reason": "invalid_record"}
    expected_url = normalize_source_url(expected.get("url") or expected.get("canonical_url"))
    actual_url = normalize_source_url(document.get("url") or document.get("canonical_url"))
    if not expected_url or not actual_url or expected_url != actual_url:
        return {"verified": False, "reason": "canonical_url_mismatch"}
    expected_title = _title_key(expected.get("title"))
    actual_title = _title_key(document.get("title"))
    if not expected_title or not actual_title:
        return {"verified": False, "reason": "title_missing"}
    expected_tokens = set(expected_title.split())
    actual_tokens = set(actual_title.split())
    if not expected_tokens.issubset(actual_tokens):
        return {"verified": False, "reason": "title_mismatch"}
    body = _body_text(document)
    if len(body) < max(1, int(min_body_chars)):
        return {"verified": False, "reason": "source_body_too_short"}
    return {
        "verified": True,
        "reason": "canonical_identity_and_body_verified",
        "document": {
            "title": str(document.get("title") or "").strip(),
            "url": str(document.get("url") or document.get("canonical_url") or "").strip(),
            "text": body,
            "source_modified": document.get("source_modified") or document.get("modified"),
        },
    }


def resolve_source_documents(
    expected_sources: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    documents: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    required_titles: tuple[str, ...] = (),
    min_verified: int = 1,
    min_body_chars: int = DEFAULT_MIN_BODY_CHARS,
) -> dict[str, Any]:
    """Resolve a bounded source set while keeping retrieval limits explicit.

    A complete set is not required unless the caller explicitly declares
    required source titles. Missing candidates never prove corpus absence.
    """
    by_url: dict[str, dict[str, Any]] = {}
    for item in documents or []:
        if not isinstance(item, dict):
            continue
        key = normalize_source_url(item.get("url") or item.get("canonical_url"))
        if key and key not in by_url:
            by_url[key] = item

    verified: list[dict[str, Any]] = []
    missing: list[str] = []
    rejected: list[dict[str, str]] = []
    for expected in expected_sources or []:
        if not isinstance(expected, dict):
            continue
        key = normalize_source_url(expected.get("url") or expected.get("canonical_url"))
        candidate = by_url.get(key) if key else None
        if candidate is None:
            missing.append(str(expected.get("title") or expected.get("url") or "unknown source"))
            continue
        result = verify_source_document(expected, candidate, min_body_chars=min_body_chars)
        if result.get("verified"):
            verified.append(result["document"])
        else:
            rejected.append({
                "title": str(expected.get("title") or "unknown source"),
                "reason": str(result.get("reason") or "verification_failed"),
            })

    verified_titles = {str(item.get("title") or "").casefold() for item in verified}
    required_missing = [
        title for title in required_titles
        if not any(title.casefold() in item_title for item_title in verified_titles)
    ]
    enough = len(verified) >= max(1, int(min_verified))
    required_ok = not required_missing
    if enough and required_ok:
        status = "complete" if not missing and not rejected else "partial"
    elif verified:
        status = "insufficient_verified_sources"
    else:
        status = "no_verified_sources"

    return {
        "version": VERSION,
        "status": status,
        "verified": bool(enough and required_ok),
        "complete": status == "complete",
        "verified_sources": verified,
        "verified_count": len(verified),
        "missing_sources": missing,
        "rejected_sources": rejected,
        "required_sources_missing": required_missing,
        "retrieval_scope": "bounded_expected_source_set",
        "corpus_absence_proven": False,
        "absence_claim_boundary": "a bounded retrieval miss does not establish that a source or protocol does not exist",
    }
