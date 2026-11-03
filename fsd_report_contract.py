"""Strict visitor-facing FSD report contract and provenance validator."""
from __future__ import annotations

import re
from typing import Any, Mapping

REPORT_KEYS = frozenset({
    "summary",
    "recurring_condition",
    "reported_signal",
    "strengths",
    "enabling_conditions",
    "constraints",
    "next_steps",
    "evidence_ids",
})
TEXT_LIMITS = {
    "summary": 900,
    "recurring_condition": 600,
    "reported_signal": 600,
}
LIST_LIMITS = {
    "strengths": 4,
    "enabling_conditions": 4,
    "constraints": 4,
    "next_steps": 4,
}
ITEM_MAX_CHARS = 300
FORBIDDEN_INTERNAL_TERMS = re.compile(r"\b(?:SEE|MOVE|REPEAT)\b", re.I)


class FSDReportContractError(ValueError):
    """Raised when model output violates the public report contract."""


def validate_fsd_report(
    report: Any,
    evidence: list[Mapping[str, Any]],
    selected_scale: str | None,
) -> dict[str, Any]:
    """Validate exact output shape and bind model references to server evidence."""
    if not isinstance(report, Mapping) or set(report) != REPORT_KEYS:
        raise FSDReportContractError("Report must contain exactly the approved fields.")
    if selected_scale is not None and selected_scale not in {
        "self", "relationships", "organization", "state", "civilization"
    }:
        raise FSDReportContractError("Selected scale is not supported.")

    evidence_by_id = {
        str(item.get("evidence_id")): item
        for item in evidence
        if isinstance(item, Mapping) and item.get("evidence_id")
    }
    if len(evidence_by_id) < 2:
        raise FSDReportContractError("Independent canonical evidence is insufficient.")

    normalized: dict[str, Any] = {}
    for key, limit in TEXT_LIMITS.items():
        value = report.get(key)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            raise FSDReportContractError(f"{key} must be non-empty bounded text.")
        value = value.strip()
        if FORBIDDEN_INTERNAL_TERMS.search(value):
            raise FSDReportContractError("Report contains prohibited internal terminology.")
        normalized[key] = value

    for key, maximum in LIST_LIMITS.items():
        values = report.get(key)
        if not isinstance(values, list) or len(values) > maximum:
            raise FSDReportContractError(f"{key} must be a bounded list.")
        clean = []
        for item in values:
            if not isinstance(item, str) or not item.strip() or len(item.strip()) > ITEM_MAX_CHARS:
                raise FSDReportContractError(f"{key} contains an invalid item.")
            value = item.strip()
            if FORBIDDEN_INTERNAL_TERMS.search(value):
                raise FSDReportContractError("Report contains prohibited internal terminology.")
            clean.append(value)
        normalized[key] = clean

    ids = report.get("evidence_ids")
    if not isinstance(ids, list) or not ids or len(ids) > 6:
        raise FSDReportContractError("At least one bounded evidence reference is required.")
    if any(not isinstance(item, str) or item not in evidence_by_id for item in ids):
        raise FSDReportContractError("Report references evidence not supplied by the server.")
    if len(set(ids)) != len(ids):
        raise FSDReportContractError("Evidence references must be unique.")

    # Do not let a model infer a multi-scale pattern from a single selected scale.
    normalized["scope"] = {
        scale: ("reported_signal" if scale == selected_scale else "not_assessed")
        for scale in ("self", "relationships", "organization", "state", "civilization")
    }
    normalized["evidence"] = [
        {
            "evidence_id": evidence_by_id[item]["evidence_id"],
            "title": evidence_by_id[item]["title"],
            "url": evidence_by_id[item]["url"],
        }
        for item in ids
    ]
    return normalized
