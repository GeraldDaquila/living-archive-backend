"""Answer-first contract for simple explanations of systemic issues.

The shared visitor boundary applies this bounded query-level repair after every
provider, retrieval, and specialist route. It preserves systemic integrity while
matching the requested explanatory depth. It never treats missing Archive
retrieval as a reason to withhold a useful general-knowledge answer.
"""
from __future__ import annotations

import re
from typing import Any, Dict


_DOORWAY = {
    "title": "Structural Frameworks",
    "url": "https://geralddaquila.com/structural-frameworks/",
    "rationale": (
        "Structural Frameworks offers a deeper continuation on the relationships "
        "and arrangements through which systems operate and change. It is a "
        "separate next step, not the evidence source for this general explanation."
    ),
}


def is_simple_systemic_explanation_question(question: Any) -> bool:
    """Match requests to explain a systemic issue simply, not incidental mentions."""
    q = re.sub(r"\s+", " ", str(question or "")).strip().casefold()
    systemic_subject = re.search(
        r"\b(?:systemic issue|systemic problem|system[- ]wide issue|"
        r"structural problem|problem rooted in the system|issue rooted in the system)\b",
        q,
    )
    explanatory_intent = re.search(
        r"\b(?:explain|describe|communicate|make|present|answer|tell|should)\b",
        q,
    )
    simplicity_request = re.search(
        r"\b(?:simple|simply|plain language|plainly|easy to understand|"
        r"straightforward|nontechnical|non-technical|brief|short answer)\b",
        q,
    )
    guide_context = re.search(r"\b(?:guide|users?|visitor|readers?|audience)\b", q)
    return bool(systemic_subject and explanatory_intent and simplicity_request and guide_context)


def build_simple_systemic_explanation_response() -> str:
    """Return the concise, answer-first explanation strategy."""
    return (
        "The Guide should make the explanation simple without making the issue "
        "simplistic. Begin with the clearest short answer: a systemic issue "
        "persists because several conditions and relationships reinforce one "
        "another, not necessarily because of one person's mistake.\n\n"
        "Then name the main mechanism in ordinary language. Briefly show which "
        "rules, incentives, resources, relationships, or feedback patterns help "
        "reproduce the problem. Use only the connections that materially explain "
        "it; distinguish what is known from what is inferred, and do not pretend "
        "that one cause explains everything.\n\n"
        "Finish with why the pattern matters and, where useful, one practical "
        "point of leverage or next step. Offer deeper layers only if the user "
        "wants them. In short: simplify the explanation, not the system."
    )


def apply_simple_systemic_explanation_boundary(question: Any, payload: Any) -> Any:
    """Repair non-answers at the shared final boundary for this bounded query family."""
    if not isinstance(payload, dict) or not is_simple_systemic_explanation_question(question):
        return payload
    if str(payload.get("intent") or "").strip().upper() in {
        "SAFETY_INTERRUPT", "SAFETY_CONVERSATION"
    }:
        return payload

    answer = build_simple_systemic_explanation_response()
    safe: Dict[str, Any] = dict(payload)
    prior_generation_present = bool(safe.get("provider") or safe.get("model"))
    no_handoff = bool(re.search(
        r"\b(?:do not|don't|without|no)\b.{0,70}\b(?:links?|resources?|recommendations?|doorways?|pages?)\b",
        str(question or ""),
        re.I,
    ))
    safe["response"] = answer
    if "answer" in safe:
        safe["answer"] = answer

    if no_handoff:
        safe["recommendation"] = None
        safe["canonical_doorway"] = None
        safe["doorway_title"] = None
        safe["doorway_url"] = None
        safe["doorway_rationale"] = None
        safe["doorway_decision"] = "omit"
        safe["doorway_omission_reason"] = "visitor_explicitly_requested_no_handoff"
    else:
        doorway = dict(_DOORWAY)
        safe["recommendation"] = doorway
        safe["canonical_doorway"] = dict(doorway)
        safe["doorway_title"] = doorway["title"]
        safe["doorway_url"] = doorway["url"]
        safe["doorway_rationale"] = doorway["rationale"]
        safe["doorway_decision"] = "include"
        safe.pop("doorway_omission_exception_reason", None)

    safe["answer_basis"] = {
        "kind": "general_knowledge",
        "label": "General knowledge",
        "explanation": (
            "This is a general explanation of how to communicate systemic issues. "
            "The separately linked Living Archive page is an optional continuation, "
            "not the evidence source for the explanation."
        ),
    }
    safe["response_provenance"] = {
        "class": "deterministic_recovery",
        "provider": "bounded_simple_systemic_explanation_contract",
        "model": None,
        "quality_adjusted_llm_eligible": False,
        "llm_invoked": prior_generation_present,
        "prior_generation_present": prior_generation_present,
    }
    safe["provider"] = None
    safe["model"] = None
    safe["evidence"] = []
    safe["evidence_validation"] = {
        "version": "1.0",
        "status": "not_applicable",
        "reason": "general_knowledge_explanation_strategy_not_source_attributed",
        "reference_count": 0,
        "claim_support": {
            "status": "not_applicable",
            "reason": "bounded_general_knowledge_explanation_strategy",
            "semantic_certification": False,
        },
        "temporal_validity": {
            "status": "not_applicable",
            "reason": "no_temporal_claims_in_response",
        },
        "semantic_certification": False,
    }
    recovery_evidence = {
        "provenance_class": "deterministic_recovery",
        "references_present": False,
        "validation_status": "not_applicable",
        "claim_support_status": "not_applicable",
        "semantic_certification": False,
    }
    envelope = safe.get("answer_envelope")
    if isinstance(envelope, dict):
        envelope = dict(envelope)
        route = dict(envelope.get("route") or {})
        route["provider_present"] = False
        route["model_present"] = False
        envelope["route"] = route
        envelope["evidence"] = recovery_evidence
        safe["answer_envelope"] = envelope
    quality_floor = safe.get("gold_star_v2_quality_floor")
    if isinstance(quality_floor, dict):
        quality_floor = dict(quality_floor)
        quality_floor["evidence_validation"] = safe["evidence_validation"]
        floor_envelope = quality_floor.get("answer_envelope")
        if isinstance(floor_envelope, dict):
            floor_envelope = dict(floor_envelope)
            floor_route = dict(floor_envelope.get("route") or {})
            floor_route["provider_present"] = False
            floor_route["model_present"] = False
            floor_envelope["route"] = floor_route
            floor_envelope["evidence"] = recovery_evidence
            quality_floor["answer_envelope"] = floor_envelope
        safe["gold_star_v2_quality_floor"] = quality_floor
    safe["response_shape"] = "simple_systemic_explanation"
    safe["simple_systemic_explanation_contract"] = {
        "version": "1.0",
        "answer_first_enforced": True,
        "retrieval_independent": True,
        "requested_depth": "simple",
        "systemic_integrity_preserved": True,
        "navigation_is_separate": not no_handoff,
    }
    safe["processing"] = "final_visitor_boundary_simple_systemic_explanation"
    safe["route_source"] = "guide_final_visitor_boundary"
    safe["visitor_boundary_version"] = safe.get("visitor_boundary_version") or "shared-systemic-explanation-contract"
    return safe
