"""Bounded answer-first recovery for institutional learning/repetition questions.

This contract repairs a narrow, high-confidence question family at the shared
final visitor boundary. It distinguishes public acknowledgment from learning
and learning from correctability. It does not diagnose a particular institution.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

VERSION = "1.0"

_DOORWAY = {
    "title": "When Experience Can Change Us: The Two Capacities of a Living System",
    "url": "https://geralddaquila.com/when-experience-can-change-us-the-two-capacities-of-a-living-system/",
    "rationale": (
        "This Living Archive essay examines how consequential experience can "
        "change an institution's understanding, and how that understanding can "
        "or cannot change the way it operates. It is a deeper continuation, "
        "not the evidence source for this general explanation."
    ),
}

_WHY = re.compile(r"\b(?:why|how come|what explains|what causes)\b", re.I)
_INSTITUTION = re.compile(
    r"\b(?:organizations?|organisations?|organizational|organisational|"
    r"institutions?|institutional|companies|agencies|governments?|nonprofits?|teams?)\b",
    re.I,
)
_RECURRENCE = re.compile(
    r"\b(?:repeat\w*|recur\w*|reproduc\w*|keep\s+(?:making|having|experiencing|"
    r"encountering|producing)|continu\w*\s+to\s+(?:make|have|experience|produce))\b",
    re.I,
)
_FAILURE = re.compile(r"\b(?:failures?|mistakes?|errors?|problems?|breakdowns?|setbacks?)\b", re.I)
_ACKNOWLEDGMENT = re.compile(
    r"\b(?:acknowledg\w*|recogniz\w*|recognis\w*|admit\w*|identified|"
    r"identify|reported|reports|publicly\s+(?:known|discussed|addressed))\b",
    re.I,
)
_NO_HANDOFF = re.compile(
    r"\b(?:do not|don't|without|no)\b.{0,70}\b"
    r"(?:links?|resources?|recommendations?|doorways?|pages?)\b",
    re.I,
)


def is_institutional_learning_failure_question(question: Any) -> bool:
    """Match causal questions about institutional recurrence after acknowledgment."""
    q = re.sub(r"\s+", " ", str(question or "")).strip()
    return bool(
        _WHY.search(q)
        and _INSTITUTION.search(q)
        and _RECURRENCE.search(q)
        and _FAILURE.search(q)
        and _ACKNOWLEDGMENT.search(q)
    )


def build_institutional_learning_failure_response() -> str:
    """Return a concise, calibrated explanation and practical diagnostic test."""
    return (
        "Because acknowledging a failure and changing the conditions that produced "
        "it are two different things. Public acknowledgment shows that a problem has "
        "been named; it does not, by itself, show that the organization has learned "
        "or become able to correct it.\n\n"
        "Several mechanisms can keep the same failure recurring:\n\n"
        "1. **Recognition without changed practice.** Reports, apologies, and public "
        "commitments may describe what went wrong while procedures, decision rules, "
        "and everyday routines remain substantially unchanged.\n\n"
        "2. **Incentives that still reward the old behavior.** Staff may be told to "
        "prevent a failure while still being rewarded for short-term targets, speed, "
        "cost-cutting, or protecting the organization's reputation. The operating "
        "incentives can outweigh the public lesson.\n\n"
        "3. **Responsibility without authority.** Many people may acknowledge the "
        "problem, but no one has clear ownership, sufficient authority, or resources "
        "to carry the correction through.\n\n"
        "4. **Information that cannot change the organization's understanding.** "
        "Bad news may be filtered, dissent discouraged, or measures chosen that hide "
        "the consequences experienced by the people affected. The organization "
        "collects information without allowing it to challenge its assumptions.\n\n"
        "5. **Lessons that never become institutional memory.** Findings may not be "
        "built into budgets, training, procedures, decision criteria, or follow-up "
        "reviews. When attention moves on or staff leave, the same conditions return.\n\n"
        "The deeper distinction is between learning to describe a failure and "
        "becoming capable of changing the system that reproduces it. Learning requires "
        "both: consequences must be able to revise what the organization understands, "
        "and that understanding must be able to change what it does.\n\n"
        "A practical test is to ask: Who owns the correction? What authority and "
        "resources do they have? Which incentive, procedure, or decision rule changed? "
        "What outcome will be measured, and when will the organization review whether "
        "the change worked? If those links are missing, acknowledgment may have "
        "occurred without effective correction.\n\n"
        "These are common mechanisms, not a diagnosis of every organization. "
        "Identifying the dominant cause in a particular case requires evidence about "
        "its decisions, incentives, accountability, and follow-through."
    )


def institutional_learning_failure_response_checks(answer: Any) -> List[Dict[str, Any]]:
    """Return observable minimum-content checks for the bounded question family."""
    text = re.sub(r"\s+", " ", str(answer or "")).casefold()
    checks = [
        {
            "name": "acknowledgment_is_distinguished_from_learning",
            "passed": bool(
                re.search(r"\b(?:acknowledg\w*|recogniz\w*|admit\w*)\b", text)
                and re.search(r"\b(?:learn\w*|correct\w*|change\w*)\b", text)
            ),
        },
        {
            "name": "structural_mechanisms_are_explained",
            "passed": bool(re.search(
                r"\b(?:incentiv\w*|authority|accountability|responsib\w*|resources?|"
                r"procedures?|routines?|structures?|power|decision rules?)\b",
                text,
            )),
        },
        {
            "name": "understanding_is_connected_to_changed_action",
            "passed": bool(
                re.search(r"\b(?:understanding|what the organization knows|what it knows)\b", text)
                and re.search(r"\b(?:action|behavior|behaviour|practice|operat\w*|does)\b", text)
                and re.search(r"\b(?:change|alter|revise|translat\w*|affect)\w*\b", text)
            ),
        },
        {
            "name": "feedback_or_institutional_memory_is_addressed",
            "passed": bool(re.search(
                r"\b(?:feedback|institutional memory|follow[- ]?up|review|"
                r"monitor\w*|measure\w*|lessons?\s+(?:are\s+)?(?:built|embedded|retained))\b",
                text,
            )),
        },
        {
            "name": "practical_corrective_test_is_offered",
            "passed": bool(
                re.search(r"\b(?:who owns|owner|responsible|accountable)\b", text)
                and re.search(r"\b(?:measure|review|track|deadline|outcome|resources?)\b", text)
            ),
        },
        {
            "name": "scope_is_calibrated",
            "passed": bool(re.search(
                r"\b(?:may|can|often|sometimes|not every|in a particular case|"
                r"depends|common mechanisms|requires evidence)\b",
                text,
            )),
        },
    ]
    return checks


def institutional_learning_failure_response_meets_contract(answer: Any) -> bool:
    checks = institutional_learning_failure_response_checks(answer)
    return bool(str(answer or "").strip()) and all(item["passed"] for item in checks)


def apply_institutional_learning_failure_boundary(question: Any, payload: Any) -> Any:
    """Repair weak answers and enforce the verified continuation at final visitor boundary."""
    if not isinstance(payload, dict) or not is_institutional_learning_failure_question(question):
        return payload
    if str(payload.get("intent") or "").strip().upper() in {
        "SAFETY_INTERRUPT", "SAFETY_CONVERSATION"
    }:
        return payload

    safe: Dict[str, Any] = dict(payload)
    current = str(safe.get("response") or safe.get("answer") or "").strip()
    needs_recovery = not institutional_learning_failure_response_meets_contract(current)
    no_handoff = bool(_NO_HANDOFF.search(str(question or "")))

    if needs_recovery:
        answer = build_institutional_learning_failure_response()
        safe["response"] = answer
        if "answer" in safe:
            safe["answer"] = answer
        prior_provenance = safe.get("response_provenance")
        prior_llm = bool(
            safe.get("provider") or safe.get("model")
            or (isinstance(prior_provenance, dict) and prior_provenance.get("llm_invoked"))
        )
        safe["response_provenance"] = {
            "class": "deterministic_recovery",
            "provider": "bounded_institutional_learning_failure_contract",
            "model": None,
            "quality_adjusted_llm_eligible": False,
            "llm_invoked": prior_llm,
            "prior_generation_present": prior_llm,
        }
        safe["provider"] = None
        safe["model"] = None
        safe["answer_basis"] = {
            "kind": "general_knowledge",
            "label": "General knowledge",
            "explanation": (
                "This is a general explanation of recurring institutional failure. "
                "The separately linked Living Archive essay is an optional continuation, "
                "not the evidence source for the explanation."
            ),
        }
        safe["evidence"] = []
        safe["evidence_validation"] = {
            "version": "1.0",
            "status": "not_applicable",
            "reason": "bounded_general_knowledge_recovery_not_source_attributed",
            "reference_count": 0,
            "claim_support": {
                "status": "not_applicable",
                "reason": "bounded_general_knowledge_recovery",
                "semantic_certification": False,
            },
            "temporal_validity": {
                "status": "not_applicable",
                "reason": "no_temporal_claims_in_response",
            },
            "semantic_certification": False,
        }

    if no_handoff:
        for key in (
            "recommendation", "canonical_doorway", "doorway_title",
            "doorway_url", "doorway_rationale",
        ):
            safe[key] = None
        safe["doorway_decision"] = "omit"
        safe["doorway_omission_reason"] = "visitor_explicitly_requested_no_handoff"
    else:
        doorway = dict(_DOORWAY)
        safe["recommendation"] = dict(doorway)
        safe["canonical_doorway"] = dict(doorway)
        safe["doorway_title"] = doorway["title"]
        safe["doorway_url"] = doorway["url"]
        safe["doorway_rationale"] = doorway["rationale"]
        safe["doorway_decision"] = "include"
        safe.pop("doorway_omission_exception_reason", None)
        safe.pop("doorway_omission_reason", None)

    safe["institutional_learning_failure_contract"] = {
        "version": VERSION,
        "matched": True,
        "answer_first_enforced": True,
        "recovery_applied": needs_recovery,
        "response_checks": institutional_learning_failure_response_checks(
            safe.get("response") or safe.get("answer")
        ),
        "doorway_is_separate_from_answer_evidence": True,
        "doorway_decision": "omit" if no_handoff else "include",
    }
    safe["response_shape"] = "institutional_learning_failure_explanation"
    safe["processing"] = (
        "final_visitor_boundary_institutional_learning_failure_recovery"
        if needs_recovery else
        "final_visitor_boundary_institutional_learning_failure_contract"
    )
    safe["route_source"] = "guide_final_visitor_boundary"
    safe["visitor_boundary_version"] = safe.get("visitor_boundary_version") or "institutional-learning-failure-v1"
    return safe
