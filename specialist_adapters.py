"""USE Specialist Adapter Contract v1.
    
Domain contributions may use a specialist-owned contract version; the adapter
layer bridges those contributions into the common Guide pipe without losing
the specialist-owned payload.


The adapter layer is the internal pipe between The Guide and a specialist
capability. It does not own routing, canonical authority, visitor-facing
prose, or the visitor session.

A specialist adapter may be implemented locally or backed by another service.
The Guide owns invocation, timeout/failure handling, contribution validation,
canonical selection, and final presentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Tuple

from boundary_resilience import preserve_specialist_payload

from specialist_registry import (
    SPECIALIST_PIPE_CONTRACT_VERSION,
    SpecialistContractError,
    get_specialist,
    specialist_invocation_allowed,
    validate_specialist_contribution,
)


SPECIALIST_ADAPTER_CONTRACT_VERSION = "v1"


@dataclass(frozen=True)
class SpecialistAdapterContext:
    """Bounded context supplied by The Guide to an adapter."""

    request_id: str
    guide_version: str
    specialist_id: str
    original_question: str
    recognized_territory: str
    processing_purpose: str
    guide_context: Mapping[str, Any]
    safety_state: Optional[str]


class SpecialistAdapter(Protocol):
    """Protocol implemented by an actual specialist integration."""

    specialist_id: str

    def process(
        self,
        context: SpecialistAdapterContext,
    ) -> Mapping[str, Any]:
        """Return an internal specialist contribution envelope."""


class SpecialistAdapterError(RuntimeError):
    """Raised when an adapter cannot complete delegated processing."""


class SpecialistAdapterRegistry:
    """Runtime registry for actual adapters.

    Registration is intentionally separate from the capability registry:
    capability says what exists; adapter says how that capability can be
    invoked. An adapter is not production-active merely because a capability
    is registered.
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, SpecialistAdapter] = {}

    def register(self, adapter: SpecialistAdapter) -> None:
        specialist_id = str(getattr(adapter, "specialist_id", "") or "").strip()

        if not specialist_id:
            raise SpecialistContractError(
                "Specialist adapter must declare specialist_id."
            )

        if get_specialist(specialist_id) is None:
            raise SpecialistContractError(
                f"Adapter references unregistered specialist: {specialist_id!r}"
            )

        if specialist_id in self._adapters:
            raise SpecialistContractError(
                f"Specialist adapter already registered: {specialist_id!r}"
            )

        self._adapters[specialist_id] = adapter

    def get(self, specialist_id: str) -> Optional[SpecialistAdapter]:
        return self._adapters.get(str(specialist_id or "").strip())

    def available(self, specialist_id: str) -> bool:
        return (
            specialist_invocation_allowed(specialist_id)
            and str(specialist_id or "").strip() in self._adapters
        )

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._adapters.keys())


def invoke_specialist(
    adapter_registry: SpecialistAdapterRegistry,
    *,
    request_id: str,
    guide_version: str,
    specialist_id: str,
    original_question: str,
    recognized_territory: str,
    processing_purpose: str,
    guide_context: Optional[Mapping[str, Any]] = None,
    safety_state: Optional[str] = None,
) -> Dict[str, Any]:
    """Invoke one adapter and return a validated internal contribution.

    This function deliberately does not:
    - choose whether the specialist should be invoked;
    - choose canonical resources;
    - generate visitor-facing prose;
    - expose specialist identity to the visitor;
    - replace the Guide response.

    Those remain Guide responsibilities.
    """

    specialist_id = str(specialist_id or "").strip()

    if not specialist_invocation_allowed(specialist_id):
        raise SpecialistAdapterError(
            f"Specialist capability is not runtime-available: {specialist_id!r}"
        )

    adapter = adapter_registry.get(specialist_id)
    if adapter is None:
        raise SpecialistAdapterError(
            f"No adapter is registered for specialist: {specialist_id!r}"
        )

    context = SpecialistAdapterContext(
        request_id=str(request_id),
        guide_version=str(guide_version),
        specialist_id=specialist_id,
        original_question=str(original_question),
        recognized_territory=str(recognized_territory),
        processing_purpose=str(processing_purpose),
        guide_context=dict(guide_context or {}),
        safety_state=safety_state,
    )

    try:
        raw_contribution = adapter.process(context)
    except Exception as exc:
        raise SpecialistAdapterError(
            f"Specialist adapter failed for {specialist_id!r}: {exc}"
        ) from exc

    # Domain specialists may have their own contribution contract. The common
    # Guide -> specialist pipe remains v1, so bridge a domain contribution into
    # the common envelope here while preserving the complete specialist-owned
    # payload for the Hub to carry without semantic loss.
    raw_contract_version = str(
        raw_contribution.get("contract_version") or ""
    ).strip()
    if raw_contract_version != SPECIALIST_PIPE_CONTRACT_VERSION:
        domain_payload = preserve_specialist_payload(raw_contribution)
        raw_contribution = {
            "contract_version": SPECIALIST_PIPE_CONTRACT_VERSION,
            "request_id": context.request_id,
            "specialist_id": context.specialist_id,
            "status": domain_payload.get("status"),
            "voice_policy": domain_payload.get("voice_policy"),
            "canonical_candidates": domain_payload.get("canonical_candidates"),
            "boundary_notes": domain_payload.get("boundary_notes"),
            "safety_flags": domain_payload.get("safety_flags"),
            # The complete domain contribution remains intact. The common pipe
            # only adds ownership metadata; it never rewrites specialist text.
            "payload": domain_payload,
        }

    return validate_specialist_contribution(
        raw_contribution,
        expected_request_id=context.request_id,
        expected_specialist_id=context.specialist_id,
    )


def adapter_contract_snapshot(
    adapter_registry: SpecialistAdapterRegistry,
) -> Dict[str, Any]:
    """Return internal diagnostics without exposing visitor-facing data."""

    return {
        "adapter_contract_version": SPECIALIST_ADAPTER_CONTRACT_VERSION,
        "pipe_contract_version": SPECIALIST_PIPE_CONTRACT_VERSION,
        "registered_adapter_ids": list(adapter_registry.ids()),
    }
