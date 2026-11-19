"""Guide-owned route capability declarations for Gold Star v2.

Declarations describe the operational scope and limits of a route. They do
not certify that a particular answer is correct, complete, or semantically
adequate. Specialist adapter implementation and integrity boundaries remain
owned by their existing modules.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

VERSION = "1.0"

# Each record is deliberately narrow. Task-family labels describe the kind of
# operation a route is designed to perform, not a guarantee for every query.
_ROUTE_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "guide_basic_inquiry": {
        "route_class": "guide_composition",
        "supported_task_families": ["explanation", "analysis", "comparison", "synthesis", "drafting", "planning", "summarization"],
        "unsupported_task_families": ["unverified_live_facts", "actions_requiring_external_authority", "tasks_outside_available_evidence"],
        "evidence_modes": ["retrieved_archive_context", "provider_generated_general_knowledge", "explicit_uncertainty"],
        "abstention_modes": ["clarification", "evidence_limitation", "provider_unavailable", "safety_handoff"],
        "scope": "General Guide composition through the provider-neutral composition seam; task-specific adequacy and evidence remain subject to validation.",
    },
    "guide_basic_inquiry_recovery": {
        "route_class": "deterministic_recovery",
        "supported_task_families": ["bounded_recovery", "limited_explanation"],
        "unsupported_task_families": ["open_ended_research", "complex_multi_source_synthesis", "unverified_live_facts"],
        "evidence_modes": ["bounded_local_recovery_context", "general_knowledge_with_limits"],
        "abstention_modes": ["recovery_limit", "clarification", "evidence_limitation"],
        "scope": "Provider-exhaustion recovery only; must not imitate a full provider answer where the deterministic recovery cannot complete the task.",
    },
    "guide_broad_conceptual_boundary": {
        "route_class": "purpose_built_deterministic",
        "supported_task_families": ["bounded_conceptual_definition"],
        "unsupported_task_families": ["open_ended_analysis", "personalized_advice", "multi_source_research", "live_facts"],
        "evidence_modes": ["predefined_general_knowledge"],
        "abstention_modes": ["outside_boundary", "clarification"],
        "scope": "A narrowly matched stable conceptual-definition boundary; not a general deterministic answer engine.",
    },
    "guide_early_deterministic_boundary": {
        "route_class": "purpose_built_deterministic",
        "supported_task_families": ["named_bounded_contract_response"],
        "unsupported_task_families": ["unmatched_questions", "open_ended_research", "live_facts"],
        "evidence_modes": ["predefined_contract_content"],
        "abstention_modes": ["outside_boundary", "clarification"],
        "scope": "Only the explicitly registered early deterministic contracts in the Guide runtime.",
    },
    "guide_direct_attribute_fail_closed": {
        "route_class": "controlled_failure",
        "supported_task_families": [],
        "unsupported_task_families": ["unsupported_direct_attribute_claim"],
        "evidence_modes": ["archive_evidence_absence"],
        "abstention_modes": ["fail_closed", "evidence_limitation"],
        "scope": "A fail-closed boundary when available Archive evidence does not establish a requested attribute; it is not an answer capability.",
    },
    "guide_final_visitor_boundary": {
        "route_class": "visitor_boundary_recovery",
        "supported_task_families": ["response_contamination_recovery", "bounded_clarity_recovery"],
        "unsupported_task_families": ["new_domain_research", "independent_task_completion"],
        "evidence_modes": ["validated_existing_payload", "bounded_general_knowledge_recovery"],
        "abstention_modes": ["withhold_contaminated_payload", "evidence_limitation"],
        "scope": "Last-mile repair of contaminated or structurally unsafe visitor output; not a primary subject-matter composer.",
    },
    "guide_missing_context_guard": {
        "route_class": "controlled_recovery",
        "supported_task_families": ["clarification_request"],
        "unsupported_task_families": ["substantive_answer_without_required_subject"],
        "evidence_modes": ["missing_context_detection"],
        "abstention_modes": ["clarification"],
        "scope": "Requests only the missing context needed to proceed; it does not answer the unresolved substantive question.",
    },
    "guide_explicit_home_navigation": {
        "route_class": "navigation_handoff",
        "supported_task_families": ["explicit_home_navigation"],
        "unsupported_task_families": ["substantive_domain_answer"],
        "evidence_modes": ["fixed_canonical_home_destination"],
        "abstention_modes": ["invalid_or_unavailable_destination"],
        "scope": "Directly fulfills an explicit request to navigate to the Living Archive homepage.",
    },
    "registry_specific_destination": {
        "route_class": "registered_destination",
        "supported_task_families": ["explicit_registered_destination_navigation"],
        "unsupported_task_families": ["substantive_domain_answer", "inferred_destination_without_explicit_intent"],
        "evidence_modes": ["canonical_guide_node_registry"],
        "abstention_modes": ["no_verified_destination", "ambiguous_destination"],
        "scope": "Routes only explicit destination requests to a canonical registered node.",
    },
    "deterministic-systems-preparation-entry": {
        "route_class": "specialist_handoff",
        "supported_task_families": ["bounded_philippine_systems_orientation"],
        "unsupported_task_families": ["unrelated_domain_tasks", "unbounded_general_research"],
        "evidence_modes": ["philippine_systems_specialist_contribution_contract"],
        "abstention_modes": ["specialist_unavailable", "invalid_contribution", "scope_mismatch"],
        "scope": "Guide-owned entry to the bounded Philippine Systems Lens contribution; the Guide retains final visitor-response authority.",
    },
    "deterministic-formation-preparation-entry": {
        "route_class": "specialist_handoff",
        "supported_task_families": ["stewardship_formation_orientation"],
        "unsupported_task_families": ["unrelated_domain_tasks", "unbounded_general_research"],
        "evidence_modes": ["formation_specialist_contribution_contract"],
        "abstention_modes": ["specialist_unavailable", "invalid_contribution", "scope_mismatch"],
        "scope": "Guide-owned entry to the bounded Formation specialist contribution; the Guide retains final visitor-response authority.",
    },
    "guide_sitewide_safety_boundary": {
        "route_class": "safety_route",
        "supported_task_families": ["safety_interrupt", "immediate_risk_routing"],
        "unsupported_task_families": ["ordinary_archive_exploration_during_active_safety_interrupt"],
        "evidence_modes": ["safety_state_machine", "verified_emergency_resource_contract"],
        "abstention_modes": ["location_required_for_local_resource", "emergency_service_handoff"],
        "scope": "Interrupts ordinary routing for detected safety concerns; must not invent local emergency contacts.",
    },
    "guide_hypothetical_safety_calibration": {
        "route_class": "safety_calibration",
        "supported_task_families": ["hypothetical_safety_routing_explanation"],
        "unsupported_task_families": ["personal_crisis_assessment_without_disclosure", "invented_local_hotline"],
        "evidence_modes": ["predefined_safety_routing_contract"],
        "abstention_modes": ["location_limitation", "clarification"],
        "scope": "Explains hypothetical safety routing and is not a live personal-crisis classification.",
    },
    "bounded_safety_conversation": {
        "route_class": "safety_route",
        "supported_task_families": ["bounded_safety_conversation"],
        "unsupported_task_families": ["ordinary_archive_retrieval", "unbounded_clinical_assessment"],
        "evidence_modes": ["bounded_safety_conversation_protocol"],
        "abstention_modes": ["emergency_handoff", "scope_limit"],
        "scope": "Bounded safety-conversation path; separate from ordinary retrieval and general composition.",
    },
}


def route_capability(route_source: str) -> Dict[str, Any]:
    """Return a defensive copy of a declared route capability, or unknown."""
    key = str(route_source or "").strip()
    record = _ROUTE_CAPABILITIES.get(key)
    if record is None:
        return {
            "version": VERSION,
            "route_source": key or "not_declared",
            "declaration_status": "not_declared",
            "route_class": "unclassified",
            "supported_task_families": [],
            "unsupported_task_families": [],
            "evidence_modes": [],
            "abstention_modes": ["unknown_route"],
            "scope": "No capability declaration is registered for this route.",
            "semantic_competence_certified": False,
        }
    return {
        "version": VERSION,
        "route_source": key,
        "declaration_status": "declared",
        **{name: list(value) if isinstance(value, list) else value for name, value in record.items()},
        "semantic_competence_certified": False,
    }


def registered_route_sources() -> tuple[str, ...]:
    """Return stable route identifiers for inventory reconciliation."""
    return tuple(sorted(_ROUTE_CAPABILITIES))


def validate_route_capability_registry(
    observed_route_sources: Any = None,
) -> Dict[str, Any]:
    """Check declaration structure and optionally reconcile observed routes."""
    errors = []
    list_fields = (
        "supported_task_families",
        "unsupported_task_families",
        "evidence_modes",
        "abstention_modes",
    )
    for route, record in _ROUTE_CAPABILITIES.items():
        for field in list_fields:
            if not isinstance(record.get(field), list) or any(
                not isinstance(item, str) or not item.strip()
                for item in record.get(field, [])
            ):
                errors.append(f"{route}:{field}")
        if not str(record.get("scope") or "").strip():
            errors.append(f"{route}:scope")
    observed = set(str(item).strip() for item in (observed_route_sources or []) if str(item).strip())
    registered = set(_ROUTE_CAPABILITIES)
    return {
        "valid": not errors,
        "errors": errors,
        "observed_unregistered": sorted(observed - registered),
        "registered_unobserved": sorted(registered - observed) if observed else [],
        "semantic_certification": False,
    }



_SPECIALIST_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "relationship": {
        "status": "available_native_guide_path",
        "supported_task_families": ["bounded_relational_perspective"],
        "unsupported_task_families": ["clinical_diagnosis", "unbounded_third_party_mind_reading"],
        "evidence_modes": ["visitor_supplied_context", "bounded_relational_contract"],
        "abstention_modes": ["insufficient_context", "safety_handoff", "scope_limit"],
        "scope": "Relationship capability is retained in the native Guide path; no separate visitor-facing HRN adapter is invoked.",
    },
    "formation": {
        "status": "available_adapter_backed",
        "supported_task_families": ["stewardship_formation_orientation", "learning_and_practice_reflection"],
        "unsupported_task_families": ["unrelated_domain_tasks", "unbounded_general_research"],
        "evidence_modes": ["formation_contribution_contract", "visitor_supplied_context"],
        "abstention_modes": ["specialist_unavailable", "invalid_contribution", "scope_mismatch"],
        "scope": "Bounded formation contribution returned to the Guide for integration; the specialist does not own the final visitor response.",
    },
    "catalogue": {
        "status": "available_native_navigation",
        "supported_task_families": ["explicit_stewardship_catalogue_navigation"],
        "unsupported_task_families": ["substantive_domain_answer"],
        "evidence_modes": ["canonical_catalogue_search"],
        "abstention_modes": ["no_verified_catalogue_destination", "ambiguous_request"],
        "scope": "Native catalogue navigation surface; it is not a registered adapter-backed reasoning route.",
    },
    "systems_ph": {
        "status": "available_adapter_backed",
        "supported_task_families": ["bounded_philippine_systems_orientation", "interacting_systems_analysis"],
        "unsupported_task_families": ["unrelated_geographies_without_evidence", "unbounded_general_research"],
        "evidence_modes": ["philippine_systems_contribution_contract", "visitor_supplied_context"],
        "abstention_modes": ["specialist_unavailable", "invalid_contribution", "scope_mismatch"],
        "scope": "Bounded Philippine systems contribution returned to the Guide for integration; the Guide retains final visitor-response authority.",
    },
    "safety": {
        "status": "available_adapter_backed_utility",
        "supported_task_families": ["bounded_safety_utility", "resource_and_state_support"],
        "unsupported_task_families": ["ordinary_archive_retrieval", "clinical_diagnosis"],
        "evidence_modes": ["safety_utility_contract", "verified_emergency_resource_contract"],
        "abstention_modes": ["location_required_for_local_resource", "emergency_service_handoff", "scope_limit"],
        "scope": "Bounded safety utility contribution under the Guide safety state machine; not a general-purpose answer specialist.",
    },
}


def specialist_capability(specialist_id: str) -> Dict[str, Any]:
    """Return bounded capability metadata for a registered specialist identity."""
    key = str(specialist_id or "").strip()
    record = _SPECIALIST_CAPABILITIES.get(key)
    if record is None:
        return {
            "version": VERSION,
            "specialist_id": key or "not_declared",
            "declaration_status": "not_declared",
            "supported_task_families": [],
            "unsupported_task_families": [],
            "evidence_modes": [],
            "abstention_modes": ["unknown_specialist"],
            "scope": "No specialist capability declaration is registered.",
            "semantic_competence_certified": False,
        }
    return {
        "version": VERSION,
        "specialist_id": key,
        "declaration_status": "declared",
        **{name: list(value) if isinstance(value, list) else value for name, value in record.items()},
        "semantic_competence_certified": False,
    }


def registered_specialist_ids() -> tuple[str, ...]:
    return tuple(sorted(_SPECIALIST_CAPABILITIES))
