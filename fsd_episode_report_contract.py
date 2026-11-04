"""Episode-report contract with strict separation of respondent account and archive context."""
from __future__ import annotations

import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from fsd_episode_contract import interpret_episode

REPORT_KEYS = frozenset({
    "summary", "episode_observation", "strengths", "enabling_conditions",
    "constraints", "next_steps", "archive_reference_ids",
})
TEXT_LIMITS = {"summary": 700, "episode_observation": 700}
LIST_LIMITS = {"strengths": 4, "enabling_conditions": 4, "constraints": 4, "next_steps": 4}
ITEM_MAX_CHARS = 260
FORBIDDEN_INTERNAL_TERMS = re.compile(r"\b(?:SEE|MOVE|REPEAT)\b")
FORBIDDEN_PROVENANCE_CLAIMS = re.compile(
    r"\b(?:archive|living archive)\b.{0,80}\b(?:verif(?:y|ies|ied)|confirm(?:s|ed)?|corroborat(?:e|es|ed))\b"
    r"|\b(?:verif(?:y|ies|ied)|confirm(?:s|ed)?|corroborat(?:e|es|ed))\b.{0,80}\b(?:episode|respondent|event)\b",
    re.I,
)


class FSDEpisodeReportError(ValueError):
    """Raised when a generated episode report violates provenance or scope."""


def validate_episode_report(
    report: Any,
    episode: Mapping[str, Any],
    archive_references: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate model composition and bind Archive references as context only."""
    if not isinstance(report, Mapping) or set(report) != REPORT_KEYS:
        raise FSDEpisodeReportError("Report must contain exactly the approved fields.")

    refs_by_id = {}
    for ref in archive_references:
        if not isinstance(ref, Mapping):
            continue
        ref_id = str(ref.get("reference_id") or "")
        title = str(ref.get("title") or "").strip()
        url = str(ref.get("url") or "").strip()
        parsed = urlsplit(url)
        if (
            ref_id and title and parsed.scheme.casefold() == "https"
            and parsed.netloc.casefold() == "geralddaquila.com"
        ):
            refs_by_id[ref_id] = {"reference_id": ref_id, "title": title, "url": url}
    if len(refs_by_id) > 6:
        refs_by_id = dict(list(refs_by_id.items())[:6])

    normalized: dict[str, Any] = {}
    for key, limit in TEXT_LIMITS.items():
        value = report.get(key)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            raise FSDEpisodeReportError(f"{key} must be non-empty bounded text.")
        value = value.strip()
        if FORBIDDEN_INTERNAL_TERMS.search(value):
            raise FSDEpisodeReportError("Report contains prohibited internal terminology.")
        if FORBIDDEN_PROVENANCE_CLAIMS.search(value):
            raise FSDEpisodeReportError("Archive references cannot be represented as episode corroboration.")
        normalized[key] = value

    for key, maximum in LIST_LIMITS.items():
        values = report.get(key)
        if not isinstance(values, list) or len(values) > maximum:
            raise FSDEpisodeReportError(f"{key} must be a bounded list.")
        clean = []
        for value in values:
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > ITEM_MAX_CHARS:
                raise FSDEpisodeReportError(f"{key} contains an invalid item.")
            value = value.strip()
            if FORBIDDEN_INTERNAL_TERMS.search(value):
                raise FSDEpisodeReportError("Report contains prohibited internal terminology.")
            if FORBIDDEN_PROVENANCE_CLAIMS.search(value):
                raise FSDEpisodeReportError("Archive references cannot be represented as episode corroboration.")
            clean.append(value)
        normalized[key] = clean

    ids = report.get("archive_reference_ids")
    if not isinstance(ids, list) or len(ids) > 6:
        raise FSDEpisodeReportError("Archive reference IDs must be a bounded list.")
    if any(not isinstance(ref_id, str) or ref_id not in refs_by_id for ref_id in ids):
        raise FSDEpisodeReportError("Report references an unavailable Archive reference.")
    if len(set(ids)) != len(ids):
        raise FSDEpisodeReportError("Archive references must be unique.")

    normalized["episode_interpretation"] = interpret_episode(episode)
    normalized["episode_provenance"] = {
        "label": "Respondent-reported account",
        "independently_verified": False,
        "scope": "One bounded episode at the selected system boundary",
    }
    normalized["archive_references"] = [
        {**refs_by_id[ref_id], "role": "conceptual_context_only"}
        for ref_id in ids
    ]
    normalized["archive_reference_notice"] = (
        "Living Archive references explain the concepts; they do not verify "
        "that the reported episode occurred or corroborate the respondent's account."
    )
    normalized["inference_limit"] = (
        "This report describes one respondent-reported episode. It does not "
        "establish stable system capacity, causation, or performance beyond this episode."
    )
    return normalized
