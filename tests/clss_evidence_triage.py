"""Conservative evidence triage for the CLSS deterministic path.

This module deliberately does not infer semantic contradictions from arbitrary
natural-language answers. It identifies evidence gaps and mixed-source/repair
conditions that can be established from explicit dimensions and provenance.
All other cases remain unresolved until a semantic reasoning component exists.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

ALLOWED_MODES = {"self", "third_party"}
ALLOWED_DIMENSIONS = {
    "commitment", "conduct", "consequences", "coherence",
    "accountability", "counterevidence", "correction", "unknown",
}
ALLOWED_SOURCES = {
    "self_report", "first_hand_observation", "documented_outcome",
    "second_hand_report", "interpretation", "unknown",
}


def triage_evidence(
    evidence: Sequence[Mapping[str, Any]],
    *,
    mode: str,
    missing_dimensions: Sequence[str] = (),
) -> dict[str, Any]:
    """Return a conservative, evidence-linked triage result, not a final finding."""
    if mode not in ALLOWED_MODES:
        raise ValueError("mode must be self or third_party")
    if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes)):
        raise ValueError("evidence must be a sequence of evidence objects")

    normalized = []
    seen: set[str] = set()
    for item in evidence:
        if not isinstance(item, Mapping):
            raise ValueError("each evidence item must be an object")
        evidence_id = item.get("evidence_id")
        dimension = item.get("dimension")
        source_type = item.get("source_type")
        answer_text = item.get("answer_text")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("every evidence item needs a non-empty evidence_id")
        if evidence_id in seen:
            raise ValueError("evidence IDs must be unique")
        if dimension not in ALLOWED_DIMENSIONS:
            raise ValueError(f"invalid evidence dimension: {dimension}")
        if source_type not in ALLOWED_SOURCES:
            raise ValueError(f"invalid evidence source_type: {source_type}")
        if not isinstance(answer_text, str) or not answer_text.strip():
            raise ValueError("every evidence item needs answer_text")
        seen.add(evidence_id)
        normalized.append({
            "evidence_id": evidence_id,
            "dimension": dimension,
            "source_type": source_type,
            "answer_text": answer_text.strip(),
        })

    unknown_dimensions = sorted(set(missing_dimensions))
    ids = [item["evidence_id"] for item in normalized]
    dimensions = {item["dimension"] for item in normalized}
    interpretive_only = bool(normalized) and all(
        item["source_type"] in {"interpretation", "unknown"}
        for item in normalized
    )
    has_concern = "conduct" in dimensions or "accountability" in dimensions
    has_correction = "correction" in dimensions
    has_counterevidence = "counterevidence" in dimensions

    # Only flag a provenance conflict when differing source positions concern
    # the same dimension. Different sources covering different dimensions are
    # not, by themselves, contradictory.
    sources_by_dimension: dict[str, set[str]] = {}
    for item in normalized:
        sources_by_dimension.setdefault(item["dimension"], set()).add(item["source_type"])
    same_dimension_source_conflict = any(
        "second_hand_report" in source_types
        and "first_hand_observation" in source_types
        for source_types in sources_by_dimension.values()
    )

    if not normalized or unknown_dimensions or "unknown" in dimensions or interpretive_only:
        category = "insufficient_evidence"
        reason = "The available material does not establish enough observable, attributable evidence for a defensible conclusion."
    elif has_concern and (has_correction or has_counterevidence):
        category = "mixed_evidence"
        reason = "The evidence includes both a concern-related dimension and a correction or counterevidence dimension; both must be examined."
    elif same_dimension_source_conflict:
        category = "mixed_evidence"
        reason = "Different source positions address the same dimension; provenance must remain distinct and any disagreement unresolved until checked."
    else:
        category = "insufficient_evidence"
        reason = "A final coherence judgment requires contextual comparison of the actual obligation, conduct, and effects; this deterministic triage does not infer that comparison from keywords."

    if mode == "third_party" and not normalized:
        reason += " The third party's private intent remains unknown."

    return {
        "mode": mode,
        "triage_type": category,
        "evidence_ids": ids,
        "missing_dimensions": unknown_dimensions,
        "reason": reason,
        "is_final_coherence_finding": False,
        "limitations": [
            "This is evidence triage, not the complete CLSS reasoning layer.",
            "No private intent, motive, suitability, or adverse inference is produced.",
            "Supported-tension and no-defensible-tension conclusions require contextual reasoning beyond this deterministic triage.",
        ],
    }
