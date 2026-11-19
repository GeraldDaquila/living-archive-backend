"""Shared Gold Star v2 answer-envelope and route-capability contract.

This module records observable route/provenance facts without claiming that a
route has semantic competence merely because it returned an answer. Unknown
routes remain explicitly unknown. Structured handoffs and errors are distinct
from completed visitor answers.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

VERSION = "1.0"

# These are transport/route classifications, not claims of semantic quality.
_ROUTE_CLASSES = {
    "guide_basic_inquiry": "guide_composition",
    "guide_basic_inquiry_recovery": "deterministic_recovery",
    "guide_broad_conceptual_boundary": "purpose_built_deterministic",
    "guide_early_deterministic_boundary": "purpose_built_deterministic",
    "guide_direct_attribute_fail_closed": "controlled_failure",
    "guide_final_visitor_boundary": "visitor_boundary_recovery",
    "guide_missing_context_guard": "controlled_recovery",
    "guide_explicit_home_navigation": "navigation_handoff",
    "registry_specific_destination": "registered_destination",
    "deterministic-formation-preparation-entry": "specialist_handoff",
    "guide_sitewide_safety_boundary": "safety_route",
    "guide_hypothetical_safety_calibration": "safety_calibration",
    "bounded_safety_conversation": "safety_route",
}

# The response route may provide a capability declaration in future versions.
# Absence is not interpreted as support for every task.
_REQUIRED_CAPABILITY_FIELDS = (
    "supported_task_families",
    "unsupported_task_families",
    "evidence_modes",
    "abstention_modes",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def build_answer_envelope(
    query: str,
    payload: Any,
    question_contract: Mapping[str, Any],
    *,
    exact_standard: bool = False,
) -> Dict[str, Any]:
    """Build privacy-conscious metadata for a completed answer or handoff."""
    body = _mapping(payload)
    if body.get("ok") is False:
        state = "error"
    elif body.get("handoff_pending") is True or (
        body.get("handoff")
        and not str(body.get("response") or body.get("answer") or "").strip()
    ):
        state = "structured_handoff"
    elif str(body.get("response") or body.get("answer") or "").strip():
        state = "completed_answer"
    else:
        state = "incomplete"

    route_source = str(body.get("route_source") or "").strip()
    route_class = _ROUTE_CLASSES.get(route_source, "unclassified")
    provenance = _mapping(body.get("response_provenance"))
    provider = str(body.get("provider") or provenance.get("provider") or "").strip()
    model = str(body.get("model") or provenance.get("model") or "").strip()
    declared = _mapping(body.get("answer_capabilities"))
    declaration_complete = all(
        isinstance(declared.get(key), (list, tuple))
        for key in _REQUIRED_CAPABILITY_FIELDS
    )

    doorway = body.get("recommendation") or body.get("doorway")
    if isinstance(doorway, Mapping) and str(doorway.get("url") or "").strip():
        doorway_state = "present_requires_canonical_validation"
    elif body.get("doorway_omission_reason"):
        doorway_state = "intentionally_omitted_with_reason"
    else:
        doorway_state = "not_declared"

    return {
        "version": VERSION,
        "state": state,
        "question_contract_version": str(question_contract.get("version") or ""),
        "route": {
            "source": route_source or "not_declared",
            "class": route_class,
            "provider_present": bool(provider),
            "model_present": bool(model),
        },
        "capability": {
            "declaration_status": "complete" if declaration_complete else "not_declared",
            "supported_task_families": list(declared.get("supported_task_families") or []) if declaration_complete else [],
            "unsupported_task_families": list(declared.get("unsupported_task_families") or []) if declaration_complete else [],
            "evidence_modes": list(declared.get("evidence_modes") or []) if declaration_complete else [],
            "abstention_modes": list(declared.get("abstention_modes") or []) if declaration_complete else [],
            "semantic_competence_certified": False,
        },
        "evidence": {
            "provenance_class": str(provenance.get("class") or "not_declared"),
            "references_present": bool(body.get("evidence") or body.get("sources") or body.get("source_documents")),
        },
        "doorway": {
            "state": doorway_state,
            "separate_from_answer": True,
            "prohibited_by_question_contract": bool(
                _mapping(question_contract.get("constraints")).get("no_handoff")
            ),
        },
        "governance": {
            "exact_standard_immutable": bool(exact_standard),
            "query_present": bool(str(query or "").strip()),
        },
    }


def validate_answer_envelope(envelope: Any) -> Dict[str, Any]:
    """Validate metadata shape only; never certify answer quality."""
    if not isinstance(envelope, dict):
        return {"valid": False, "reason": "not_object"}
    required = ("version", "state", "question_contract_version", "route",
                "capability", "evidence", "doorway", "governance")
    missing = [key for key in required if key not in envelope]
    if missing:
        return {"valid": False, "reason": "missing_fields", "missing": missing}
    if envelope.get("version") != VERSION:
        return {"valid": False, "reason": "unsupported_version"}
    if envelope.get("state") not in {
        "completed_answer", "structured_handoff", "error", "incomplete"
    }:
        return {"valid": False, "reason": "invalid_state"}
    return {"valid": True, "reason": "schema_valid_not_quality_certified"}
