"""Stewardship Formation -> The Guide contribution grammar v1.

This contribution boundary ports the bounded Formation navigator mechanism into
the common specialist pipe. It is structured navigation material, not a
diagnosis and not visitor-ready prose owned by The Guide.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

FORMATION_CONTRIBUTION_CONTRACT_VERSION = "formation-v1"
FORMATION_VOICE_POLICY = "preserve_specialist_boundary"

_ALLOWED_STATUSES = frozenset({
    "CONTRIBUTION",
    "NO_CONTRIBUTION",
    "DECLINED",
    "FAILED",
})


class FormationContributionError(ValueError):
    """Raised when a Formation contribution violates its contract."""


def validate_formation_contribution(
    contribution: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(contribution, Mapping):
        raise FormationContributionError("Formation contribution must be a mapping.")

    status = str(contribution.get("status") or "").strip().upper()
    if status not in _ALLOWED_STATUSES:
        raise FormationContributionError(
            f"Unsupported formation contribution status: {status!r}"
        )

    interpretation = contribution.get("interpretation")
    movement = contribution.get("movement")
    canonical_candidates = contribution.get("canonical_candidates")

    if interpretation is not None and not isinstance(interpretation, Mapping):
        raise FormationContributionError("interpretation must be a mapping.")
    if movement is not None and not isinstance(movement, Mapping):
        raise FormationContributionError("movement must be a mapping.")
    if canonical_candidates is not None and not isinstance(
        canonical_candidates, (list, tuple)
    ):
        raise FormationContributionError("canonical_candidates must be a list.")

    normalized = {
        "contract_version": FORMATION_CONTRIBUTION_CONTRACT_VERSION,
        "status": status,
        "voice_policy": FORMATION_VOICE_POLICY,
        "interpretation": dict(interpretation or {}),
        "perspectives": list(contribution.get("perspectives") or []),
        "movement": dict(movement or {}),
        "canonical_candidates": list(canonical_candidates or []),
        "boundary_notes": contribution.get("boundary_notes"),
        "safety_flags": contribution.get("safety_flags"),
    }

    if status == "CONTRIBUTION" and not (
        normalized["interpretation"] or normalized["canonical_candidates"]
    ):
        raise FormationContributionError(
            "A usable Formation contribution needs interpretation or canonical candidates."
        )

    return normalized


def formation_contract_snapshot() -> Dict[str, Any]:
    return {
        "formation_contribution_contract_version":
            FORMATION_CONTRIBUTION_CONTRACT_VERSION,
        "voice_policy": FORMATION_VOICE_POLICY,
        "t4_destination_allowed": False,
        "diagnostic_claims": False,
        "three_door_limit": True,
    }
