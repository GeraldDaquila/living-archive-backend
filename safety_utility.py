"""Sitewide Safety / Crisis utility backed by the existing HRN safety system."""
from __future__ import annotations
from typing import Any, Mapping

from safety_intelligence import (
    SAFETY_INTELLIGENCE_CONTRACT_VERSION,
    classify_safety,
    resolve_safety,
    safety_intelligence_snapshot,
)

SAFETY_UTILITY_VERSION = "v2"

def build_safety_contribution(
    *,
    request_id: str,
    query: str,
    safety_state: str,
    country: str = "",
    history: str = "",
    safety_question: str = "",
) -> Mapping[str, Any]:
    state = str(safety_state or "current").strip().casefold()
    resolution = resolve_safety(
        query=query,
        history=history,
        safety_state=state,
        country=country,
        safety_question=safety_question or query,
    )
    return {
        "contract_version": "v1",
        "request_id": str(request_id),
        "specialist_id": "safety",
        "status": "CONTRIBUTION",
        "voice_policy": "preserve_hrn_safety_system",
        "canonical_candidates": [],
        "boundary_notes": {
            "utility_version": SAFETY_UTILITY_VERSION,
            "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
            "sitewide": True,
            "priority": "highest",
            "bypasses_ordinary_hrn": True,
            "bypasses_llm": True,
            "bypasses_retrieval": True,
            "resource_owner": "Emergency Intelligence",
            "language_owner": "HRN Safety Fractal",
            "resolver_status": resolution.get("resolver_status", "hrn_emergency_intelligence"),
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
            "display_mode": "hrn_safety",
            "safety_message": resolution.get("safety_message") or "",
            "safety_question": resolution.get("safety_question") or "",
            "safety_note": resolution.get("safety_note") or "",
            "safety_resources": list(resolution.get("safety_resources") or []),
            "safety_location_required": bool(resolution.get("safety_location_required")),
            "country": resolution.get("country") or country,
            "safety_release_ready": bool(resolution.get("safety_release_ready")),
            "resources": list(resolution.get("safety_resources") or []),
            "next_movement": resolution.get("safety_question") or "",
            "resolver_status": resolution.get("resolver_status", "hrn_emergency_intelligence"),
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
        "hrn_dependency": True,
        "hrn_role": "closest_sibling_safety_intelligence_provider",
        "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
        "safety_intelligence": snapshot,
    }
