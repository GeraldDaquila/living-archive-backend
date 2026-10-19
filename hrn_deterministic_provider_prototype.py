"""Experimental, bounded HRN deterministic reasoning provider.

This module is an isolated prototype, not wired into the live WordPress plugin.
It deliberately supports only a narrow, explicit relational scenario and returns
insufficient_context outside that scope instead of pretending to be an LLM.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


CONTRACT_VERSION = "hrn-reasoning-result/0.1"
PROVIDER_ID = "deterministic-relational-prototype"
ALLOWED_MOVES = {"clarify", "distinguish", "deepen", "reflect", "close"}


def reason(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return a provider-neutral result without mutating the supplied snapshot."""
    original = deepcopy(snapshot)
    message = str(original.get("visitor_message") or "").strip()
    if not message:
        return _result(
            status="insufficient_context",
            snapshot=original,
            move="clarify",
            evidence=[],
            observations=[],
            interpretation="There is not enough visitor input to interpret safely.",
            rationale="The current visitor message is empty.",
            response="I don't yet have enough to understand the situation. What would you most like me to understand?",
            limitations=["empty_visitor_message"],
        )

    prior_questions = original.get("prior_questions") or []
    prior_moves = original.get("prior_moves") or []
    turn = int(original.get("turn_number") or 1)
    lower = message.casefold()

    # Deliberately narrow supported scenario: a friend became distant after
    # the visitor declined a request for a loan.
    loan_timing = any(
        term in lower
        for term in (
            "declined loan",
            "declined lending",
            "declined to lend",
            "refused to lend",
            "said no to lending",
            "loaning them some money",
            "lend them some money",
        )
    )
    silence_pattern = any(
        term in lower
        for term in (
            "ghosting",
            "long silence",
            "evaded answers",
            "aloof",
            "not responding",
            "ignoring my texts",
        )
    )

    if loan_timing and turn >= 2:
        evidence = ["loan_decision_timing"]
        observations = [
            "The visitor noticed the distance after declining to lend money."
        ]
        response = (
            "The timing after you declined to lend the money stands out, "
            "though timing alone cannot tell us whether that caused the distance. "
            "Did your friend connect their change in behavior to your decision, "
            "or have they left that connection unspoken?"
        )
        move = "distinguish"
        interpretation = (
            "The visitor reports a temporal association between declining a loan "
            "and the friend's distance; causation remains unknown."
        )
        rationale = "Separate the reported timing from an unverified causal explanation."
        limitations = ["temporal_association_is_not_causation"]
        status = "success"
    elif silence_pattern and turn >= 3 and "distinguish" in prior_moves:
        evidence = ["ongoing_silence", "evasive_answers", "uncertain_trigger"]
        observations = [
            "The visitor describes continued silence and answers that do not address the concern.",
            "The visitor does not know when the change began or what triggered it.",
        ]
        response = (
            "The silence and evasive answers leave you with two uncertainties: "
            "what began the distance, and whether your friend is willing to talk "
            "about it now. Those are related, but not the same question. When you "
            "have asked about the distance directly, how have they responded?"
        )
        move = "deepen"
        interpretation = (
            "The trigger is unclear; the next useful distinction is whether the "
            "friend engages when the distance itself is raised."
        )
        rationale = "Advance from guessing the trigger to observing willingness to address the issue."
        limitations = ["trigger_unknown", "friend_motive_unknown"]
        status = "success"
    elif turn == 1 and any(term in lower for term in ("friend", "friendship")):
        evidence = ["relationship_distance_concern"]
        observations = ["The visitor wants to understand a change in a friendship."]
        response = (
            "Noticing distance in a friendship can leave you unsure whether to "
            "reach out or give the other person room. We do not yet know what the "
            "distance means. What has changed most noticeably in how your friend responds?"
        )
        move = "clarify"
        interpretation = "The visitor is seeking orientation about a friendship."
        rationale = "Begin with observable behavior before interpreting motive."
        limitations = ["reason_for_distance_unknown"]
        status = "success"
    else:
        return _result(
            status="insufficient_context",
            snapshot=original,
            move="clarify",
            evidence=[],
            observations=[],
            interpretation="This scenario is outside the deterministic prototype's supported rules.",
            rationale="Avoid making unsupported semantic inferences outside the narrow tested case.",
            response="I don't want to assume more than we know. Could you share one concrete moment that would help me understand what changed?",
            limitations=["outside_supported_deterministic_scope"],
        )

    current_signature = _normalize_question(response)
    if any(current_signature == _normalize_question(str(q)) for q in prior_questions):
        return _result(
            status="insufficient_context",
            snapshot=original,
            move="clarify",
            evidence=evidence,
            observations=observations,
            interpretation=interpretation,
            rationale="The proposed response repeats a prior question and cannot safely advance this journey.",
            response="I may be circling the same question. What feels most important to understand that we haven't yet addressed?",
            limitations=limitations + ["repetition_guard_triggered"],
        )

    return _result(
        status=status,
        snapshot=original,
        move=move,
        evidence=evidence,
        observations=observations,
        interpretation=interpretation,
        rationale=rationale,
        response=response,
        limitations=limitations,
    )


def _normalize_question(value: str) -> str:
    import re

    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", value.casefold()).split())


def _result(
    *,
    status: str,
    snapshot: dict[str, Any],
    move: str,
    evidence: list[str],
    observations: list[str],
    interpretation: str,
    rationale: str,
    response: str,
    limitations: list[str],
) -> dict[str, Any]:
    if move not in ALLOWED_MOVES:
        raise ValueError(f"Unsupported move: {move}")
    return {
        "contract_version": CONTRACT_VERSION,
        "provider_id": PROVIDER_ID,
        "provider_version": "0.1.0",
        "status": status,
        "request_id": snapshot.get("request_id"),
        "session_id": snapshot.get("session_id"),
        "visitor_turn_id": snapshot.get("visitor_turn_id"),
        "evidence_delta": evidence,
        "observations": observations,
        "interpretation": interpretation,
        "distinctions": ["Visitor-reported observations are not proof of another person's motive."],
        "next_move": move,
        "move_rationale": rationale,
        "response_draft": response,
        "proposed_state_delta": {
            "turn_number": snapshot.get("turn_number"),
            "last_move": move,
            "evidence_references": evidence,
        },
        "limitations": limitations,
    }
