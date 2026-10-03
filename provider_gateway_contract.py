"""Bounded provider capability contract for specialist services.

The Guide does not choose or invoke an LLM provider for a specialist. The
specialist service owns its provider gateway. This module records only the
transport capabilities the Guide may expect from a multi-provider specialist.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple


PROVIDER_GATEWAY_CONTRACT_VERSION = "v1"
SUPPORTED_STRUCTURED_PROVIDERS: Tuple[str, ...] = (
    "groq",
    "qwen",
    "gemini",
)


def provider_gateway_capabilities() -> Dict[str, Any]:
    """Return non-secret provider capability metadata."""
    return {
        "contract_version": PROVIDER_GATEWAY_CONTRACT_VERSION,
        "providers": list(SUPPORTED_STRUCTURED_PROVIDERS),
        "selection_owner": "specialist_service",
        "transport_owner": "specialist_service",
        "guide_never_receives_provider_credentials": True,
    }
