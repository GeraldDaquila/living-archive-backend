"""Versioned, episode-based FSD request contract.

This is a candidate v2 contract. It records one bounded episode and makes no
capacity score or stable system inference. It is intentionally side-effect free.
"""
from __future__ import annotations

from typing import Any, Mapping

CONTRACT_VERSION = "fsd-episode-v1"

SCALES = frozenset({"self", "relationships", "community", "institution", "civilization"})
ENUMS = {
    "prior_understanding": frozenset({"clear", "partial", "disputed", "unknown"}),
    "experience_type": frozenset({"observed_outcome", "affected_party_feedback", "documented_evidence", "repeated_pattern", "unexpected_consequence", "other_unclear"}),
    "consequence_significance": frozenset({"material_outcome_or_decision", "material_risk_or_mismatch", "limited_or_ambiguous", "unclear"}),
    "understanding_after": frozenset({"revised", "qualified", "examined_and_retained", "not_reconsidered", "no_opportunity", "unknown"}),
    "reconsideration_basis": frozenset({"directly_changed_explanation", "prompted_examination", "considered_with_competing_evidence", "no_clear_connection", "unknown"}),
    "subsequent_response": frozenset({"decision_or_action_changed", "tested_or_piloted", "paused_pending_evidence", "no_response", "attempted_but_blocked", "too_early_or_unknown"}),
    "understanding_action_link": frozenset({"directly_informed", "partly_informed", "unrelated_or_unclear", "no_response_or_unknown"}),
    "response_available": frozenset({"yes", "partly", "no", "unknown"}),
    "non_change_reason": frozenset({"not_warranted", "more_evidence_needed", "authority_or_resources_unavailable", "competing_responsibilities_or_risks", "resistance_or_existing_arrangements", "insufficient_time", "unclear", "not_applicable"}),
}
TEXT_LIMITS = {"prior_understanding_detail": 240, "experience_detail": 360}
REQUIRED_FIELDS = frozenset({"contract_version", "scale", *ENUMS.keys()})
ALLOWED_FIELDS = REQUIRED_FIELDS | frozenset(TEXT_LIMITS)


class FSDEpisodeContractError(ValueError):
    """Raised when an episode request violates the v2 input contract."""


def validate_episode_payload(payload: Any) -> dict[str, Any]:
    """Validate a complete structured account of one episode.

    Optional descriptions are short and bounded. All interpretations are
    derived downstream; clients cannot submit scores, diagnoses, evidence,
    provider settings, or conclusions.
    """
    if not isinstance(payload, Mapping):
        raise FSDEpisodeContractError("Request must be a JSON object.")
    if set(payload) - ALLOWED_FIELDS:
        raise FSDEpisodeContractError("Request contains unsupported fields.")
    if not REQUIRED_FIELDS.issubset(payload):
        raise FSDEpisodeContractError("Episode request is missing required fields.")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise FSDEpisodeContractError("Unsupported FSD episode contract version.")

    scale = payload.get("scale")
    if not isinstance(scale, str) or scale not in SCALES:
        raise FSDEpisodeContractError("A supported system boundary must be selected.")

    normalized: dict[str, Any] = {"contract_version": CONTRACT_VERSION, "scale": scale}
    for field, allowed in ENUMS.items():
        value = payload.get(field)
        if not isinstance(value, str) or value not in allowed:
            raise FSDEpisodeContractError(f"{field} must be a supported selection.")
        normalized[field] = value

    for field, limit in TEXT_LIMITS.items():
        value = payload.get(field, "")
        if not isinstance(value, str):
            raise FSDEpisodeContractError(f"{field} must be text.")
        value = value.strip()
        if len(value) > limit:
            raise FSDEpisodeContractError(f"{field} exceeds its character limit.")
        normalized[field] = value

    # Consistency guard: an asserted consequential response cannot be described
    # as having no relationship only when the respondent selected no response.
    response = normalized["subsequent_response"]
    link = normalized["understanding_action_link"]
    if response in {"no_response", "too_early_or_unknown"} and link in {"directly_informed", "partly_informed"}:
        raise FSDEpisodeContractError("A response link cannot be selected when no response is reported.")
    if response in {"decision_or_action_changed", "tested_or_piloted", "paused_pending_evidence", "attempted_but_blocked"} and link == "no_response_or_unknown":
        raise FSDEpisodeContractError("Select the reported relationship to the subsequent response.")

    # The non-change reason is applicable only when no response followed or
    # the response was blocked/paused; otherwise require not_applicable.
    non_change_context = response in {"no_response", "attempted_but_blocked", "paused_pending_evidence", "too_early_or_unknown"}
    reason = normalized["non_change_reason"]
    if not non_change_context and reason != "not_applicable":
        raise FSDEpisodeContractError("Non-change reason must be not_applicable when a response occurred.")
    if non_change_context and reason == "not_applicable":
        raise FSDEpisodeContractError("Select a reason or unclear when response was absent, blocked, paused, or too early.")

    return normalized


def interpret_episode(payload: Mapping[str, Any]) -> dict[str, str]:
    """Return cautious episode-level labels; never a capacity score."""
    item = validate_episode_payload(payload)
    correspondence = (
        item["experience_type"] != "other_unclear"
        and item["consequence_significance"] in {"material_outcome_or_decision", "material_risk_or_mismatch"}
        and item["understanding_after"] in {"revised", "qualified", "examined_and_retained"}
        and item["reconsideration_basis"] in {"directly_changed_explanation", "prompted_examination", "considered_with_competing_evidence"}
    )
    if item["understanding_after"] in {"unknown", "no_opportunity"} or item["consequence_significance"] == "unclear":
        correspondence_label = "insufficient_evidence"
    elif correspondence:
        correspondence_label = "reported"
    else:
        correspondence_label = "not_demonstrated_in_episode"

    response = item["subsequent_response"]
    meaningful_opportunity = item["response_available"] in {"yes", "partly"}
    linked_response = (
        response in {"decision_or_action_changed", "tested_or_piloted"}
        and item["understanding_action_link"] in {"directly_informed", "partly_informed"}
    )
    if not correspondence_label == "reported":
        correctability_label = "not_assessable_without_correspondence"
    elif response == "too_early_or_unknown" or item["response_available"] == "unknown":
        correctability_label = "insufficient_evidence"
    elif not meaningful_opportunity:
        correctability_label = "not_assessable_response_unavailable"
    elif linked_response:
        correctability_label = "reported"
    elif item["non_change_reason"] == "not_warranted":
        correctability_label = "no_change_warranted"
    elif item["non_change_reason"] in {"more_evidence_needed", "insufficient_time"}:
        correctability_label = "deferred_pending_evidence_or_time"
    elif response in {"no_response", "attempted_but_blocked", "paused_pending_evidence"}:
        correctability_label = "constraint_or_delay_reported"
    else:
        correctability_label = "not_demonstrated_in_episode"

    if correspondence_label == "insufficient_evidence" or correctability_label == "insufficient_evidence":
        overall = "insufficient_evidence"
    elif correspondence_label == "reported" and correctability_label == "reported":
        overall = "both_transitions_reported"
    elif correspondence_label == "reported":
        overall = "correspondence_reported_correctability_not_demonstrated"
    else:
        overall = "neither_transition_demonstrated_in_episode"

    return {
        "correspondence": correspondence_label,
        "correctability": correctability_label,
        "overall": overall,
        "scope": item["scale"],
        "inference_boundary": "one_episode_only_no_stable_system_capacity_claim",
    }
