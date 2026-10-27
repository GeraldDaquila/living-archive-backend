"""Provider-neutral CLSS reasoning boundary.

This module does not make network calls and does not claim to reason by itself.
A caller may supply an already-approved local candidate builder; its output is
always checked against the shared response contract before it can be returned.
The deterministic fallback is used for builder errors or invalid candidates.
This module is not wired into the WordPress plugin or production request path.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from tests.clss_deterministic_response import build_deterministic_response
from tests.clss_response_validator import validate_or_fallback

CandidateBuilder = Callable[
    [Sequence[Mapping[str, Any]], str],
    Mapping[str, Any],
]


def resolve_clss_response(
    evidence: Sequence[Mapping[str, Any]],
    *,
    mode: str,
    candidate_builder: CandidateBuilder | None = None,
    missing_dimensions: Sequence[str] = (),
) -> dict[str, Any]:
    """Return a validated candidate or validated fallback; never call a provider.

    The injected builder is an integration seam, not a provider integration.
    Network transport, privacy consent, and persistence are intentionally outside
    this function and remain prohibited unless separately approved.
    """
    fallback = build_deterministic_response(
        evidence,
        mode=mode,
        missing_dimensions=missing_dimensions,
    )
    candidate: Any = None
    if candidate_builder is not None:
        try:
            candidate = candidate_builder(evidence, mode)
        except Exception:
            # Provider/local-builder failures must not leak raw errors or output.
            candidate = None

    accepted, selected_path = validate_or_fallback(
        candidate,
        fallback,
        {item["evidence_id"] for item in evidence},
        mode=mode,
    )
    result = dict(accepted)
    result["path"] = selected_path
    return result
