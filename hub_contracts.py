"""Post-Oct. 1 Guide hub contracts.

This module is intentionally small and authority-light. It defines the
shared language between The Guide and specialist spokes without importing
legacy USE routing, provider selection, retrieval, or visitor-facing prose.

The hub validates capability identity and specialist contributions. It does
not decide how a specialist reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional
from boundary_resilience import preserve_specialist_payload


HUB_CONTRACT_VERSION = "v1"
_ALLOWED_STATUSES = frozenset({"CONTRIBUTION", "NO_CONTRIBUTION", "DECLINED", "FAILED"})


@dataclass(frozen=True)
class HubRequest:
    request_id: str
    guide_version: str
    original_question: str
    recognized_territory: str
    processing_purpose: str
    guide_context: Mapping[str, Any] = field(default_factory=dict)
    safety_state: Optional[str] = None


@dataclass(frozen=True)
class HubContribution:
    request_id: str
    specialist_id: str
    status: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    voice_policy: str = ""
    canonical_candidates: tuple[Mapping[str, Any], ...] = ()


class HubContractError(ValueError):
    pass


def build_hub_request(
    *,
    request_id: str,
    guide_version: str,
    original_question: str,
    recognized_territory: str,
    processing_purpose: str,
    guide_context: Optional[Mapping[str, Any]] = None,
    safety_state: Optional[str] = None,
) -> HubRequest:
    """Create the common Guide -> spoke request envelope."""
    question = str(original_question or "").strip()
    if not question:
        raise HubContractError("Hub request requires original_question.")

    return HubRequest(
        request_id=str(request_id or "").strip(),
        guide_version=str(guide_version or "").strip(),
        original_question=question,
        recognized_territory=str(recognized_territory or "").strip(),
        processing_purpose=str(processing_purpose or "").strip(),
        guide_context=dict(guide_context or {}),
        safety_state=None if safety_state is None else str(safety_state).strip(),
    )


def validate_hub_contribution(
    contribution: Mapping[str, Any],
    *,
    expected_request_id: str,
    expected_specialist_id: str,
) -> HubContribution:
    """Validate the generic specialist -> hub envelope.

    Domain-specific contribution validators remain responsible for specialist
    semantics. This layer validates only common ownership metadata.
    """
    if not isinstance(contribution, Mapping):
        raise HubContractError("Hub contribution must be a mapping.")

    contract_version = str(contribution.get("contract_version") or "").strip()
    if contract_version != HUB_CONTRACT_VERSION:
        raise HubContractError("Unsupported or missing hub contract version.")

    request_id = str(contribution.get("request_id") or "").strip()
    if request_id != str(expected_request_id):
        raise HubContractError("Hub contribution request_id mismatch.")

    specialist_id = str(contribution.get("specialist_id") or "").strip()
    if specialist_id != str(expected_specialist_id):
        raise HubContractError("Hub contribution specialist_id mismatch.")

    status = str(contribution.get("status") or "").strip().upper()
    if status not in {"CONTRIBUTION", "NO_CONTRIBUTION", "DECLINED", "FAILED"}:
        raise HubContractError(f"Unsupported hub contribution status: {status!r}.")

    # Preserve the full domain contribution inside the generic hub envelope.
    # The hub must not collapse specialist-owned fields such as human_response
    # or journey state into a single interpretation mapping.
    payload = contribution.get("payload")
    if payload is None:
        payload = {
            key: value
            for key, value in contribution.items()
            if key not in {
                "contract_version",
                "request_id",
                "specialist_id",
                "status",
                "voice_policy",
                "canonical_candidates",
            }
        }
    if not isinstance(payload, Mapping):
        raise HubContractError("Hub contribution payload must be a mapping.")
    try:
        payload = preserve_specialist_payload(payload)
    except (TypeError, ValueError) as exc:
        raise HubContractError(f"Hub contribution payload preservation failed: {exc}") from exc

    candidates = contribution.get("canonical_candidates") or []
    if not isinstance(candidates, (list, tuple)):
        raise HubContractError("Hub canonical_candidates must be a list.")

    return HubContribution(
        request_id=request_id,
        specialist_id=specialist_id,
        status=status,
        payload=dict(payload),
        voice_policy=str(contribution.get("voice_policy") or "").strip(),
        canonical_candidates=tuple(
            item for item in candidates if isinstance(item, Mapping)
        ),
    )


def route_spoke(
    *,
    request: HubRequest,
    specialist_id: str,
    invoke: Callable[..., Mapping[str, Any]],
    recognized_territory: Optional[str] = None,
) -> HubContribution:
    """Invoke one spoke through the hub boundary and validate its return."""
    target = str(specialist_id or "").strip()
    if not target:
        raise HubContractError("A spoke identity is required.")

    raw = invoke(
        request_id=request.request_id,
        guide_version=request.guide_version,
        specialist_id=target,
        original_question=request.original_question,
        recognized_territory=recognized_territory or request.recognized_territory,
        processing_purpose=request.processing_purpose,
        guide_context=request.guide_context,
        safety_state=request.safety_state,
    )
    return validate_hub_contribution(
        raw,
        expected_request_id=request.request_id,
        expected_specialist_id=target,
    )


def hub_contract_snapshot() -> dict[str, Any]:
    """Return non-secret diagnostics for the Guide hub boundary."""
    return {
        "hub_contract_version": HUB_CONTRACT_VERSION,
        "topology": {
            "hub": "guide_use",
            "spokes": "specialist_capabilities",
            "legacy_general_utility": "legacy_use_pre_oct_1",
        },
        "authority": {
            "routing": "guide",
            "specialist_reasoning": "spoke",
            "canonical_navigation": "guide",
            "final_visitor_response": "guide",
        },
    }
