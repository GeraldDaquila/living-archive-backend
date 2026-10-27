"""Human-confirmed contextual comparison for CLSS.

This is a structured reasoning/review layer, not an NLP model. It refuses to
infer semantic relationships from keywords. A reviewer (or future approved
reasoner with separately evaluated semantic fidelity) must explicitly supply
the comparison judgments and evidence references. This module has no network or
persistence behavior.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tests.clss_response_validator import validate_candidate_response

FINDING_TYPES = {
    "supported_tension",
    "mixed_evidence",
    "insufficient_evidence",
    "no_defensible_tension",
}
ALIGNMENTS = {"supports_tension", "aligns", "unclear"}
CONTEXT_STATUSES = {"material", "not_material", "unknown"}
REPAIR_STATUSES = {"material_repair", "no_repair_evidence", "unknown"}
SOURCE_STATUSES = {"consistent", "conflict", "not_applicable", "unknown"}


class ContextualReviewError(ValueError):
    """Raised when a contextual review is incomplete or unsupported."""


def compose_contextual_review(
    evidence: Sequence[Mapping[str, Any]],
    review: Mapping[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    """Compose a cited CLSS response from explicit, human-confirmed comparisons."""
    if mode not in {"self", "third_party"}:
        raise ContextualReviewError("mode must be self or third_party")
    if not isinstance(review, Mapping):
        raise ContextualReviewError("review must be an object")
    evidence_by_id = {item.get("evidence_id"): item for item in evidence}
    if not evidence_by_id or None in evidence_by_id:
        raise ContextualReviewError("evidence must have valid evidence IDs")

    def ids(field: str, required: bool = True) -> list[str]:
        value = review.get(field, [])
        if not isinstance(value, (list, tuple)) or (required and not value):
            raise ContextualReviewError(f"{field} must be a non-empty list")
        if not all(isinstance(v, str) and v in evidence_by_id for v in value):
            raise ContextualReviewError(f"{field} contains an unknown evidence ID")
        if len(set(value)) != len(value):
            raise ContextualReviewError(f"{field} must not contain duplicate IDs")
        return list(value)

    obligation_ids = ids("obligation_evidence_ids", required=False)
    conduct_ids = ids("conduct_evidence_ids", required=False)
    effect_ids = ids("effect_evidence_ids", required=False)
    counter_ids = ids("counterevidence_ids", required=False)
    context_ids = ids("context_evidence_ids", required=False)
    repair_ids = ids("repair_evidence_ids", required=False)
    source_conflict_ids = ids("source_conflict_evidence_ids", required=False)

    alignment = review.get("alignment")
    context_status = review.get("context_status")
    repair_status = review.get("repair_status")
    source_status = review.get("source_status")
    if alignment not in ALIGNMENTS:
        raise ContextualReviewError("alignment must be supports_tension, aligns, or unclear")
    if context_status not in CONTEXT_STATUSES:
        raise ContextualReviewError("invalid context_status")
    if repair_status not in REPAIR_STATUSES:
        raise ContextualReviewError("invalid repair_status")
    if source_status not in SOURCE_STATUSES:
        raise ContextualReviewError("invalid source_status")

    rationale = review.get("rationale")
    action = review.get("next_action")
    indicators = review.get("observable_indicators")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ContextualReviewError("rationale must explain the contextual comparison")
    if not isinstance(action, str) or not action.strip():
        raise ContextualReviewError("next_action must be concrete")
    if not isinstance(indicators, list) or not indicators or not all(
        isinstance(x, str) and x.strip() for x in indicators
    ):
        raise ContextualReviewError("observable_indicators must be a non-empty list of text")

    # A documented source conflict can be reported as mixed evidence even when
    # the full obligation-conduct-effect chain is not yet available. It must not
    # be promoted into a final stewardship-tension finding without that chain.
    enough_comparison = bool(obligation_ids and conduct_ids and effect_ids)
    if source_status == "conflict":
        finding = "mixed_evidence"
        central_text = (
            "The accounts conflict on a material point. Preserve the source distinction "
            "and verify the disputed detail before treating either account as settled."
        )
    elif not enough_comparison or alignment == "unclear":
        finding = "insufficient_evidence"
        central_text = (
            "The available evidence does not yet establish a defensible conclusion "
            "about coherence. The missing link is identified below; its absence is "
            "not evidence against the person."
        )
    elif alignment == "supports_tension" and (
        context_status == "material" or repair_status == "material_repair" or counter_ids
    ):
        finding = "mixed_evidence"
        central_text = (
            "The evidence supports a possible tension between the service obligation "
            "and conduct, while material context or counterevidence also needs to be "
            "weighed. The concern should be examined directly without treating it as settled."
        )
    elif alignment == "supports_tension":
        finding = "supported_tension"
        central_text = (
            "The reviewed evidence supports a tension between the stated service "
            "obligation, the described conduct, and its reported effects."
        )
    elif alignment == "aligns":
        finding = "no_defensible_tension"
        central_text = (
            "The evidence reviewed currently aligns with the relevant service obligation; "
            "the material supplied does not establish a defensible incoherence."
        )
    else:
        finding = "insufficient_evidence"
        central_text = "The available evidence does not yet establish a defensible conclusion about coherence."

    all_ids = list(dict.fromkeys(
        obligation_ids + conduct_ids + effect_ids + counter_ids + context_ids +
        repair_ids + source_conflict_ids
    ))
    if not all_ids:
        raise ContextualReviewError("review must cite at least one evidence item")

    evidence_lines = []
    for evidence_id in all_ids:
        item = evidence_by_id[evidence_id]
        evidence_lines.append({
            "text": (
                f"{evidence_id} ({item.get('dimension', 'unknown')}; "
                f"source: {item.get('source_type', 'unknown')}): "
                f"{item.get('answer_text', '')}"
            ),
            "evidence_ids": [evidence_id],
        })

    interpretation_text = rationale.strip()
    if mode == "third_party":
        interpretation_text += (
            " This assessment concerns observable alignment with role obligations; "
            "the person's private intent remains unknown unless directly and appropriately attributed."
        )
    if context_status == "unknown":
        unknown_text = "Relevant context remains unknown and could change the interpretation."
    elif repair_status == "unknown":
        unknown_text = "Whether subsequent correction or repair occurred remains unknown."
    elif source_status == "conflict":
        unknown_text = "The conflicting accounts remain unresolved; neither is treated as settled."
    else:
        unknown_text = "Any additional material context or counterevidence should be recorded before finalizing the interpretation."
    unknown_ids = list(dict.fromkeys(counter_ids + context_ids + repair_ids + source_conflict_ids)) or all_ids

    candidate = {
        "mode": mode,
        "path": "llm",
        "central_incoherence": {
            "text": central_text,
            "finding_type": finding,
            "evidence_ids": all_ids,
        },
        "why_it_matters": {
            "text": interpretation_text,
            "evidence_ids": list(dict.fromkeys(obligation_ids + conduct_ids + effect_ids)) or all_ids,
        },
        "what_the_evidence_says": evidence_lines,
        "what_could_change_the_interpretation": [{
            "text": unknown_text,
            "evidence_ids": unknown_ids,
        }],
        "what_to_do_next": {
            "action": action.strip(),
            "owner": review.get("next_action_owner") if isinstance(review.get("next_action_owner"), str) else None,
            "observable_indicators": indicators,
        },
        "limits": [
            "The finding depends on the explicit contextual review supplied; this module does not infer semantic relationships from raw answer text.",
            "No suitability decision or private-motive conclusion is made.",
        ],
    }
    validated = validate_candidate_response(candidate, set(evidence_by_id), mode=mode, path="llm")
    validated["path"] = "deterministic_fallback"
    return validated
