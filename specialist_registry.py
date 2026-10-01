"""USE Specialist Capability Registry and Pipe Contract v1.

This module defines the internal boundary between The Guide and bounded
specialist capabilities. It deliberately contains no visitor-facing UI,
specialist prompts, retrieval logic, model selection, or network transport.

The Guide remains the owner of the visitor request and final experience.
Specialists provide bounded contributions that return to The Guide for
validation and integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple


SPECIALIST_PIPE_CONTRACT_VERSION = "v1"


@dataclass(frozen=True)
class SpecialistCapability:
    """Minimal internal registry record for one delegated capability."""

    specialist_id: str
    public_name: str
    domain: str
    purpose: str
    entry_point: str
    trigger_territory: str
    access_class: str
    status: str


SPECIALIST_REGISTRY: Tuple[SpecialistCapability, ...] = (
    SpecialistCapability(
        specialist_id="relationship",
        public_name="Seeing the Relationship",
        domain="human relationships",
        purpose="Explore relational situations through multiple perspectives.",
        entry_point="relationship",
        trigger_territory="self, person-to-person, family, group, community, organization, institution, and intergroup relationships",
        access_class="public",
        status="available",
    ),
    SpecialistCapability(
        specialist_id="formation",
        public_name="Stewardship Formation Navigator",
        domain="stewardship formation",
        purpose="Explore questions of learning, practice, responsibility, and formation.",
        entry_point="formation",
        trigger_territory="questions about what a situation may be asking a person to learn, practice, examine, or carry",
        access_class="formation",
        status="planned",
    ),
    SpecialistCapability(
        specialist_id="catalogue",
        public_name="Stewardship Catalogue",
        domain="stewardship resources",
        purpose="Navigate the specialized stewardship catalogue.",
        entry_point="catalogue",
        trigger_territory="bounded questions about stewardship resources and specialized catalogue material",
        access_class="catalogue",
        status="planned",
    ),
    SpecialistCapability(
        specialist_id="systems_ph",
        public_name="Philippine Systems Lens",
        domain="Philippine systems",
        purpose="Explore complex Philippine conditions through a bounded systems lens.",
        entry_point="systems_ph",
        trigger_territory="questions whose central inquiry concerns interacting Philippine systems and conditions",
        access_class="public",
        status="planned",
    ),
    SpecialistCapability(
        specialist_id="safety",
        public_name="Safety / Crisis",
        domain="immediate safety",
        purpose="Establish safety, connection, and appropriate emergency-resource movement.",
        entry_point="safety",
        trigger_territory="acute or potentially acute safety concerns",
        access_class="safety",
        status="planned",
    ),
)


_ALLOWED_STATUS = frozenset({"planned", "available", "disabled"})
_ALLOWED_CONTRIBUTION_STATUS = frozenset(
    {"CONTRIBUTION", "NO_CONTRIBUTION", "DECLINED", "FAILED"}
)


class SpecialistContractError(ValueError):
    """Raised when a specialist contract object violates the v1 boundary."""


def registry_snapshot() -> Tuple[SpecialistCapability, ...]:
    """Return the immutable registry as a tuple."""

    return SPECIALIST_REGISTRY


def get_specialist(specialist_id: str) -> Optional[SpecialistCapability]:
    """Return one registered capability by internal ID."""

    target = str(specialist_id or "").strip()
    for capability in SPECIALIST_REGISTRY:
        if capability.specialist_id == target:
            return capability
    return None


def available_specialists() -> Tuple[SpecialistCapability, ...]:
    """Return only explicitly available capabilities.

    Planned capabilities remain invisible to runtime invocation. This prevents
    architectural registration from being mistaken for production activation.
    """

    return tuple(
        capability
        for capability in SPECIALIST_REGISTRY
        if capability.status == "available"
    )


def build_specialist_request(
    *,
    request_id: str,
    guide_version: str,
    specialist_id: str,
    original_question: str,
    recognized_territory: str,
    processing_purpose: str,
    guide_context: Optional[Mapping[str, Any]] = None,
    safety_state: Optional[str] = None,
    requested_output: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the bounded Guide -> Specialist request envelope."""

    capability = get_specialist(specialist_id)
    if capability is None:
        raise SpecialistContractError(
            f"Unknown specialist capability: {specialist_id!r}"
        )

    if capability.status != "available":
        raise SpecialistContractError(
            f"Specialist capability is not available: {specialist_id!r}"
        )

    request = {
        "contract_version": SPECIALIST_PIPE_CONTRACT_VERSION,
        "request_id": str(request_id),
        "guide_version": str(guide_version),
        "specialist_id": capability.specialist_id,
        "original_question": str(original_question),
        "recognized_territory": str(recognized_territory),
        "processing_purpose": str(processing_purpose),
        "guide_context": dict(guide_context or {}),
        "safety_state": safety_state,
        "requested_output": dict(requested_output or {}),
    }

    return request


def validate_specialist_contribution(
    contribution: Mapping[str, Any],
    *,
    expected_request_id: str,
    expected_specialist_id: str,
) -> Dict[str, Any]:
    """Validate and normalize Specialist -> Guide contribution data.

    A contribution is internal material only. This validator intentionally does
    not mark any returned prose as visitor-ready.
    """

    if not isinstance(contribution, Mapping):
        raise SpecialistContractError("Specialist contribution must be a mapping.")

    contract_version = str(contribution.get("contract_version") or "").strip()
    if contract_version != SPECIALIST_PIPE_CONTRACT_VERSION:
        raise SpecialistContractError(
            "Unsupported specialist pipe contract version."
        )

    request_id = str(contribution.get("request_id") or "").strip()
    if request_id != str(expected_request_id):
        raise SpecialistContractError(
            "Specialist contribution request_id does not match the active Guide request."
        )

    specialist_id = str(contribution.get("specialist_id") or "").strip()
    if specialist_id != str(expected_specialist_id):
        raise SpecialistContractError(
            "Specialist contribution specialist_id does not match the delegated capability."
        )

    status = str(contribution.get("status") or "").strip().upper()
    if status not in _ALLOWED_CONTRIBUTION_STATUS:
        raise SpecialistContractError(
            f"Unsupported specialist contribution status: {status!r}"
        )

    normalized = {
        "contract_version": SPECIALIST_PIPE_CONTRACT_VERSION,
        "request_id": request_id,
        "specialist_id": specialist_id,
        "status": status,
        "interpretation": contribution.get("interpretation"),
        "perspectives": contribution.get("perspectives"),
        "movement": contribution.get("movement"),
        "canonical_candidates": contribution.get("canonical_candidates"),
        "boundary_notes": contribution.get("boundary_notes"),
        "safety_flags": contribution.get("safety_flags"),
    }

    return normalized


def contribution_is_usable(contribution: Mapping[str, Any]) -> bool:
    """Return whether the contribution is eligible for Guide integration.

    This is deliberately weaker than final acceptance. The Guide still owns
    relevance, centrality, coherence, canonicality, movement, safety, and the
    final visitor response.
    """

    return str(contribution.get("status") or "").upper() == "CONTRIBUTION"


def specialist_invocation_allowed(specialist_id: str) -> bool:
    """Return whether a registered capability may be invoked by the Guide."""

    capability = get_specialist(specialist_id)
    return capability is not None and capability.status == "available"


def validate_registry() -> None:
    """Run structural invariants for the internal registry."""

    seen = set()

    for capability in SPECIALIST_REGISTRY:
        if capability.specialist_id in seen:
            raise SpecialistContractError(
                f"Duplicate specialist_id: {capability.specialist_id!r}"
            )
        seen.add(capability.specialist_id)

        if not capability.public_name.strip():
            raise SpecialistContractError(
                f"Missing public_name for {capability.specialist_id!r}"
            )

        if capability.status not in _ALLOWED_STATUS:
            raise SpecialistContractError(
                f"Invalid registry status for {capability.specialist_id!r}: "
                f"{capability.status!r}"
            )

        if not capability.domain.strip():
            raise SpecialistContractError(
                f"Missing domain for {capability.specialist_id!r}"
            )

        if not capability.purpose.strip():
            raise SpecialistContractError(
                f"Missing purpose for {capability.specialist_id!r}"
            )


validate_registry()
