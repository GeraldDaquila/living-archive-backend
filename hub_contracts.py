"""Post-Oct. 1 Guide hub contracts.

This module is intentionally small and authority-light. It defines the
shared language between The Guide and specialist spokes without importing
legacy USE routing, provider selection, retrieval, or visitor-facing prose.

The hub validates capability identity and specialist contributions. It does
not decide how a specialist reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


HUB_CONTRACT_VERSION = "v1"


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
    if contract_version and contract_version not in {HUB_CONTRACT_VERSION, "v1"}:
        raise HubContractError("Unsupported hub contract version.")

    request_id = str(contribution.get("request_id") or "").strip()
    if request_id != str(expected_request_id):
        raise HubContractError("Hub contribution request_id mismatch.")

    specialist_id = str(contribution.get("specialist_id") or "").strip()
    if specialist_id != str(expected_specialist_id):
        raise HubContractError("Hub contribution specialist_id mismatch.")

    status = str(contribution.get("status") or "").strip().upper()
    if status not in {"CONTRIBUTION", "NO_CONTRIBUTION", "DECLINED", "FAILED"}:
        raise HubContractError(f"Unsupported hub contribution status: {status!r}.")

    payload = contribution.get("payload")
    if payload is None:
        payload = contribution.get("interpretation") or {}
    if not isinstance(payload, Mapping):
        raise HubContractError("Hub contribution payload must be a mapping.")

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
