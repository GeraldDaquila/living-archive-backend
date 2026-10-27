"""Compose a conservative canonical CLSS response from triage and supplied evidence.

This is a provider-independent fallback composer, not a semantic reasoner. It
uses only evidence IDs, dimensions, source types, and answer text supplied by the
caller. It never labels a person or asserts a supported tension by inference.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tests.clss_evidence_triage import triage_evidence
from tests.clss_response_validator import validate_candidate_response


SOURCE_LABELS = {
    "self_report": "self-report",
    "first_hand_observation": "firsthand observation",
    "documented_outcome": "documented outcome",
    "second_hand_report": "secondhand report",
    "interpretation": "interpretation supplied by the respondent",
    "unknown": "unspecified source",
}


def build_deterministic_response(
    evidence: Sequence[Mapping[str, Any]],
    *,
    mode: str,
    missing_dimensions: Sequence[str] = (),
) -> dict[str, Any]:
    """Build and validate a canonical response, failing closed on empty evidence."""
    triage = triage_evidence(
        evidence, mode=mode, missing_dimensions=missing_dimensions
    )
    if not triage["evidence_ids"]:
        raise ValueError(
            "Cannot produce a cited canonical response without at least one evidence item."
        )

    by_id = {item["evidence_id"]: item for item in evidence}
    evidence_ids = triage["evidence_ids"]
    category = triage["triage_type"]

    if category == "mixed_evidence":
        central_text = (
            "The available material points in more than one direction. The concern, "
            "correction, or differing source accounts need to be examined together; "
            "this is not yet a final judgment about stewardship."
        )
        action = (
            "Review the cited accounts side by side with the people involved, "
            "preserve their different source positions, and establish what can be "
            "verified before drawing a conclusion."
        )
        indicator = (
            "The review records which details are firsthand, secondhand, documented, "
            "or disputed, and identifies any facts still unresolved."
        )
    elif category == "insufficient_evidence":
        central_text = (
            "The evidence supplied does not establish a defensible conclusion about "
            "coherence between the service obligation and conduct. This is an evidence "
            "gap, not evidence against the person."
        )
        action = (
            "Ask for one specific episode: what responsibility applied, what was "
            "actually said or done, what effect was observed, and what context or "
            "response might change the interpretation."
        )
        indicator = (
            "A concrete episode is recorded with its source, context, observable "
            "conduct, reported effect, and any relevant counterevidence."
        )
    else:
        # Defensive branch if triage expands in future: do not imply a finding.
        central_text = (
            "No final coherence finding is produced by this deterministic fallback; "
            "contextual reasoning is still required."
        )
        action = "Gather the missing context before drawing a conclusion."
        indicator = "The evidence and material unknowns are recorded for review."

    evidence_lines = []
    for item in evidence:
        source = SOURCE_LABELS[item["source_type"]]
        evidence_lines.append({
            "text": (
                f"{item['evidence_id']} ({item['dimension']}; source: {source}): "
                f"“{item['answer_text']}”"
            ),
            "evidence_ids": [item["evidence_id"]],
        })

    unknowns = []
    if missing_dimensions:
        unknowns.append({
            "text": (
                "The following dimensions were not supplied and must remain unknown: "
                + ", ".join(sorted(set(missing_dimensions)))
                + ". Their absence is not adverse evidence."
            ),
            "evidence_ids": [evidence_ids[0]],
        })
    if category == "mixed_evidence":
        unknowns.append({
            "text": (
                "The available accounts or evidence directions require verification; "
                "this fallback does not resolve the disagreement or determine motive."
            ),
            "evidence_ids": evidence_ids,
        })
    elif not unknowns:
        unknowns.append({
            "text": (
                "Whether the evidence changes when the relevant context, affected "
                "people's accounts, and subsequent actions are checked remains open."
            ),
            "evidence_ids": evidence_ids,
        })

    response = {
        "mode": mode,
        "path": "deterministic_fallback",
        "central_incoherence": {
            "text": central_text,
            "finding_type": category,
            "evidence_ids": evidence_ids,
        },
        "why_it_matters": {
            "text": (
                "A fair stewardship judgment depends on the relationship between the "
                "responsibility, the observed conduct, its effects, and relevant context. "
                "The current triage does not substitute for that comparison."
            ),
            "evidence_ids": evidence_ids,
        },
        "what_the_evidence_says": evidence_lines,
        "what_could_change_the_interpretation": unknowns,
        "what_to_do_next": {
            "action": action,
            "owner": None,
            "observable_indicators": [indicator],
        },
        "limits": list(triage["limitations"]),
    }
    return validate_candidate_response(
        response, set(evidence_ids), mode=mode, path="deterministic_fallback"
    )
