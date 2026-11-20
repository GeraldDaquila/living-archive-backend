"""Guide-specific evidence integrity gate for reflexive critique tasks.

Reject WordPress/media presentation metadata before it can enter answer
composition as if it were substantive Archive evidence. This is a relevance
and content-type boundary, not a canonical-authority selector.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.0"

_METADATA_MARKERS = (
    "data-image-caption", "data-large-file", "wp-image-", "attachment_id",
    "wp-content/uploads", "optimized webp copy", "original png retained",
    "image-caption", "media-caption", "featured image", "site header image",
)
_MARKUP_ATTRIBUTE = re.compile(
    r"""(?:\bdata-[a-z0-9_-]+\s*=|\b(?:src|srcset|alt|class|style)\s*=)""",
    re.I,
)
_TAG = re.compile(r"<\s*/?\s*[a-z][^>]*>", re.I)
_URL = re.compile(r"https?://\S+", re.I)


def is_substantive_archive_evidence(document: Any) -> bool:
    """True only for page material with enough human-readable substance."""
    if not isinstance(document, dict):
        return False
    title = str(document.get("title") or "").strip()
    body = str(
        document.get("text") or document.get("content")
        or document.get("excerpt") or ""
    ).strip()
    if not title or not body:
        return False
    folded = body.casefold()
    marker_hits = sum(marker in folded for marker in _METADATA_MARKERS)
    visible = _TAG.sub(" ", body)
    visible = _URL.sub(" ", visible)
    visible = _MARKUP_ATTRIBUTE.sub(" ", visible)
    visible = re.sub(r"[{}<>\[\]\\=\"']", " ", visible)
    visible = re.sub(r"\s+", " ", visible).strip(" ,;:-")
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", visible)
    # A caption/media fragment can contain a few readable words, but it is
    # not an argument, definition, principle, or substantive page passage.
    if marker_hits >= 1 and len(words) < 45:
        return False
    if len(words) < 25:
        return False
    if _MARKUP_ATTRIBUTE.search(body) and len(words) < 60:
        return False
    return True


def filter_critique_evidence(context: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy with non-substantive evidence removed."""
    result = dict(context or {})
    removed = 0
    retained = 0
    for key in (
        "generation_authority_protected_docs",
        "question_authority_protected_docs",
        "documents", "canonical_documents", "results", "sources", "assets",
    ):
        value = result.get(key)
        if isinstance(value, list):
            kept = [item for item in value if is_substantive_archive_evidence(item)]
            removed += len(value) - len(kept)
            retained += len(kept)
            result[key] = kept
    # Context strings are opaque formatted evidence. If the known media
    # metadata signature appears, fail closed for that block rather than pass
    # markup through to the language model.
    for key in ("context_blocks", "canonical_link_context"):
        value = result.get(key)
        if isinstance(value, str) and any(
            marker in value.casefold() for marker in _METADATA_MARKERS
        ):
            result[key] = ""
            removed += 1
    if removed:
        result["_critique_evidence_integrity"] = {
            "version": VERSION,
            "removed_non_substantive_items": removed,
            "retained_substantive_items": retained,
        }
    if removed and retained == 0:
        result["frame_neutral_evidence_unavailable"] = True
        result["question_structure_evidence_unavailable"] = True
        result["evidence_sufficiency_unavailable"] = True
        result["question_evidence_fit_unavailable"] = True
    return result


__all__ = ["VERSION", "is_substantive_archive_evidence", "filter_critique_evidence"]
