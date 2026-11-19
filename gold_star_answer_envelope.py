"""Shared Gold Star v2 answer-envelope and route-capability contract.

This module records observable route/provenance facts without claiming that a
route has semantic competence merely because it returned an answer. Unknown
routes remain explicitly unknown. Structured handoffs and errors are distinct
from completed visitor answers.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

from gold_star_route_capabilities import route_capability, specialist_capability

VERSION = "1.0"

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
    declared_capability = route_capability(route_source)
    route_class = str(declared_capability.get("route_class") or "unclassified")
    provenance = _mapping(body.get("response_provenance"))
    provider = str(body.get("provider") or provenance.get("provider") or "").strip()
    model = str(body.get("model") or provenance.get("model") or "").strip()

    specialist_payload = _mapping(
        body.get("formation_delegation") or body.get("systems_delegation")
    )
    specialist_id = str(specialist_payload.get("specialist_id") or "").strip()
    specialist_declaration = specialist_capability(specialist_id) if specialist_id else {
        "version": "",
        "specialist_id": "not_declared",
        "declaration_status": "not_declared",
        "supported_task_families": [],
        "unsupported_task_families": [],
        "evidence_modes": [],
        "abstention_modes": [],
        "scope": "No specialist contribution is declared on this response.",
        "semantic_competence_certified": False,
    }

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
            "registry_version": declared_capability.get("version", ""),
            "declaration_status": declared_capability.get("declaration_status", "not_declared"),
            "supported_task_families": list(declared_capability.get("supported_task_families") or []),
            "unsupported_task_families": list(declared_capability.get("unsupported_task_families") or []),
            "evidence_modes": list(declared_capability.get("evidence_modes") or []),
            "abstention_modes": list(declared_capability.get("abstention_modes") or []),
            "scope": declared_capability.get("scope", ""),
            "semantic_competence_certified": False,
        },
        "evidence": {
            "provenance_class": str(provenance.get("class") or "not_declared"),
            "references_present": bool(body.get("evidence") or body.get("sources") or body.get("source_documents")),
        },
        "specialist": {
            "id": specialist_declaration.get("specialist_id", "not_declared"),
            "declaration_status": specialist_declaration.get("declaration_status", "not_declared"),
            "registry_version": specialist_declaration.get("version", ""),
            "supported_task_families": list(specialist_declaration.get("supported_task_families") or []),
            "unsupported_task_families": list(specialist_declaration.get("unsupported_task_families") or []),
            "evidence_modes": list(specialist_declaration.get("evidence_modes") or []),
            "abstention_modes": list(specialist_declaration.get("abstention_modes") or []),
            "scope": specialist_declaration.get("scope", ""),
            "semantic_competence_certified": False,
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
                "capability", "evidence", "specialist", "doorway", "governance")
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
