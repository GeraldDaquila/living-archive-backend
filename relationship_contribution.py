"""Seeing the Relationship -> The Guide contribution grammar v2.

The adapter boundary preserves HRN voice and carries the relational journey
state back to The Guide without allowing Guide prose or canonical selection to
take ownership of HRN's visible experience.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping


RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION = "v2"
RELATIONSHIP_VOICE_POLICY = "preserve_specialist_voice"

_ALLOWED_STATUSES = frozenset({
    "CONTRIBUTION",
    "NO_CONTRIBUTION",
    "DECLINED",
    "FAILED",
})


class RelationshipContributionError(ValueError):
    """Raised when a relational contribution violates its contract."""


def validate_relationship_contribution(
    contribution: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate and normalize HRN contribution data."""

    if not isinstance(contribution, Mapping):
        raise RelationshipContributionError(
            "Relationship contribution must be a mapping."
        )

    status = str(contribution.get("status") or "").strip().upper()
    if status not in _ALLOWED_STATUSES:
        raise RelationshipContributionError(
            f"Unsupported relationship contribution status: {status!r}"
        )

    voice_policy = str(
        contribution.get("voice_policy") or RELATIONSHIP_VOICE_POLICY
    ).strip()
    if voice_policy != RELATIONSHIP_VOICE_POLICY:
        raise RelationshipContributionError(
            "Seeing the Relationship must use preserve_specialist_voice."
        )

    human_response = contribution.get("human_response")
    if human_response is not None and not isinstance(human_response, str):
        raise RelationshipContributionError(
            "human_response must be text when supplied."
        )

    interpretation = contribution.get("interpretation")
    if interpretation is not None and not isinstance(interpretation, Mapping):
        raise RelationshipContributionError(
            "interpretation must be a mapping when supplied."
        )

    perspectives = contribution.get("perspectives")
    if perspectives is not None and not isinstance(perspectives, (list, tuple)):
        raise RelationshipContributionError(
            "perspectives must be a list when supplied."
        )

    movement = contribution.get("movement")
    if movement is not None and not isinstance(movement, Mapping):
        raise RelationshipContributionError(
            "movement must be a mapping when supplied."
        )

    canonical_candidates = contribution.get("canonical_candidates")
    if canonical_candidates is not None and not isinstance(
        canonical_candidates, (list, tuple)
    ):
        raise RelationshipContributionError(
            "canonical_candidates must be a list when supplied."
        )

    journey = contribution.get("journey")
    if journey is not None and not isinstance(journey, Mapping):
        raise RelationshipContributionError(
            "journey must be a mapping when supplied."
        )

    normalized = {
        "contract_version": RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
        "status": status,
        "voice_policy": voice_policy,
        "human_response": human_response,
        "interpretation": dict(interpretation or {}),
        "perspectives": list(perspectives or []),
        "movement": dict(movement or {}),
        "canonical_candidates": list(canonical_candidates or []),
        "journey": dict(journey or {}),
        "boundary_notes": contribution.get("boundary_notes"),
        "safety_flags": contribution.get("safety_flags"),
    }

    if status == "CONTRIBUTION" and not human_response and not normalized["interpretation"]:
        raise RelationshipContributionError(
            "A usable relationship contribution needs human_response or interpretation."
        )

    return normalized


def relationship_contract_snapshot() -> Dict[str, Any]:
    """Return internal diagnostics for the relational contribution boundary."""

    return {
        "relationship_contribution_contract_version":
            RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
        "voice_policy": RELATIONSHIP_VOICE_POLICY,
        "guide_rewrites_specialist_voice": False,
        "guide_owns_final_canonical_selection": True,
        "journey_state_transport": True,
    }
