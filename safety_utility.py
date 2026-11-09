"""Sitewide Safety / Crisis utility backed by the standalone deterministic safety state machine."""
from __future__ import annotations
from typing import Any, Mapping

from safety_intelligence import (
    SAFETY_INTELLIGENCE_CONTRACT_VERSION,
    classify_safety,
    resolve_safety,
    safety_intelligence_snapshot,
)

SAFETY_UTILITY_VERSION = "v4"

def build_safety_contribution(
    *,
    request_id: str,
    query: str,
    safety_state: str,
    country: str = "",
    history: str = "",
    safety_question: str = "",
    unit_turns: int = 0,
    location: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    state = str(safety_state or "current").strip().casefold()
    resolution = resolve_safety(
        query=query,
        history=history,
        safety_state=state,
        country=country,
        safety_question=safety_question,
        unit_turns=unit_turns,
        location=location,
    )
    return {
        "contract_version": "v1",
        "request_id": str(request_id),
        "specialist_id": "safety",
        "status": "CONTRIBUTION",
        "voice_policy": "preserve_standalone_deterministic_safety_system",
        "canonical_candidates": [],
        "boundary_notes": {
            "utility_version": SAFETY_UTILITY_VERSION,
            "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
            "sitewide": True,
            "priority": "highest",
            "bypasses_ordinary_relational_composition": True,
            "bypasses_llm": True,
            "bypasses_retrieval": True,
            "resource_owner": "Emergency Intelligence",
            "language_owner": "Guide Standalone Deterministic Safety State Machine",
            "resolver_status": resolution.get("resolver_status", "standalone_deterministic_safety_state_machine"),
            "emergency_selection_status": resolution.get("emergency_selection_status", ""),
            "emergency_presentation": resolution.get("emergency_presentation") or {},
            "emergency_registry_authority": "Emergency Intelligence",
            "safety_loop_guard": resolution.get("loop_guard", "active"),
        },
        "safety_flags": {
            "safety": True,
            "safety_interrupt": True,
            "safety_state": resolution.get("safety") or state,
            "safety_question": resolution.get("safety_question") or "",
            "safety_release_ready": bool(resolution.get("safety_release_ready")),
            "country": resolution.get("country") or country,
        },
        "payload": {
            "human_response": resolution.get("safety_message") or "",
            "safety_interrupt": True,
            "safety_state": resolution.get("safety") or state,
            "display_mode": "safety",
            "safety_message": resolution.get("safety_message") or "",
            "safety_question": resolution.get("safety_question") or "",
            "safety_note": resolution.get("safety_note") or "",
            "safety_resources": list(resolution.get("safety_resources") or []),
            "safety_location_required": bool(resolution.get("safety_location_required")),
            "country": resolution.get("country") or country,
            "safety_release_ready": bool(resolution.get("safety_release_ready")),
            "resources": list(resolution.get("safety_resources") or []),
            "next_movement": resolution.get("safety_question") or "",
            "emergency_resolution": resolution.get("emergency_resolution") or {},
            "emergency_presentation": resolution.get("emergency_presentation") or {},
            "emergency_selection_status": resolution.get("emergency_selection_status") or "",
            "safety_presence": resolution.get("safety_presence") or "unknown",
            "safety_question_context": resolution.get("safety_question_context") or "",
            "resolver_status": resolution.get("resolver_status", "standalone_deterministic_safety_state_machine"),
        },
    }

def safety_utility_snapshot() -> dict[str, Any]:
    snapshot = safety_intelligence_snapshot()
    return {
        "utility_version": SAFETY_UTILITY_VERSION,
        "specialist_id": "safety",
        "scope": "sitewide",
        "priority": "highest",
        "routing": "deterministic_pre_routing",
        "llm": False,
        "retrieval": False,
        "hrn_dependency": False,
        "standalone_safety_state_machine": True,
        "safety_state_machine": "standalone_deterministic",
        "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
        "safety_intelligence": snapshot,
    }
