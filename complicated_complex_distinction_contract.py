"""Bounded Guide contract for the complicated-versus-complex distinction.

This contract answers a recognizable conceptual distinction at the shared
visitor boundary, independently of provider availability or retrieval success.
The Archive doorway is a separate, verified continuation and is not presented
as evidence for the general-knowledge explanation.
"""
from __future__ import annotations

import re
from typing import Any, Dict


_DOORWAY = {
    "title": "Structural Frameworks",
    "url": "https://geralddaquila.com/structural-frameworks/",
    "rationale": (
        "Structural Frameworks explores the recurring relationships and "
        "architectures through which systems adapt, coordinate, and evolve. "
        "It is a relevant Living Archive continuation after the distinction "
        "has been explained, not the evidence source for the general-knowledge answer."
    ),
}


def is_complicated_complex_distinction_question(question: Any) -> bool:
    """Match a genuine comparison of the two concepts, not incidental co-mentions."""
    q = re.sub(r"\s+", " ", str(question or "")).strip().casefold()
    if not q or not re.search(r"\bcomplicat(?:ed|ion)\b", q) or not re.search(r"\bcomplex(?:ity)?\b", q):
        return False
    contrast = re.search(
        r"\b(?:difference|differ|distinguish|distinction|contrast|versus|vs\.?|compared?|comparison|relationship)\b",
        q,
    )
    question_shape = re.search(r"\b(?:what|how|which|is|are|between)\b", q)
    return bool(contrast and question_shape)


def build_complicated_complex_response() -> str:
    """Return the bounded three-paragraph conceptual answer."""
    return (
        "A **complicated system** can have many parts and require considerable expertise, "
        "but its components and their relationships can usually be identified and analyzed. "
        "Its behavior is sufficiently stable that specialists can break the problem into "
        "parts, understand how those parts work, and often reproduce a reliable result. "
        "An aircraft engine is complicated: designing or repairing one is demanding, but "
        "the components, specifications, and causal relationships can be studied and tested.\n\n"
        "A **complex system** is different because the interactions among its parts keep "
        "shaping one another. People, organisms, or other adaptive elements respond to "
        "conditions and to each other; feedback, changing relationships, and nonlinear "
        "effects can produce outcomes that cannot be reliably predicted by examining each "
        "part separately. An ecosystem or a community is complex: understanding its "
        "elements helps, but the whole also changes through their ongoing interaction.\n\n"
        "So the distinction is not simply that one is easy and the other difficult. "
        "**Complicated means difficult but, in principle, analyzable through decomposition "
        "and expertise; complex means adaptive and emergent, so understanding develops "
        "through observation, feedback, and learning over time.** A complicated problem "
        "often benefits from specialist analysis, planning, and precise execution. A complex "
        "situation calls for listening to the system, testing proportionate interventions, "
        "watching what changes, and adapting. A real situation can contain both: its "
        "technical components may be complicated while the human or ecological system "
        "around them is complex."
    )


def apply_complicated_complex_distinction_boundary(
    question: Any, payload: Any
) -> Any:
    """Enforce the conceptual answer and a separate canonical doorway at the final boundary."""
    if not isinstance(payload, dict) or not is_complicated_complex_distinction_question(question):
        return payload
    if str(payload.get("intent") or "").strip().upper() in {
        "SAFETY_INTERRUPT", "SAFETY_CONVERSATION"
    }:
        return payload

    answer = build_complicated_complex_response()
    safe: Dict[str, Any] = dict(payload)
    safe["response"] = answer
    if "answer" in safe:
        safe["answer"] = answer
    doorway = dict(_DOORWAY)
    safe["recommendation"] = doorway
    safe["canonical_doorway"] = dict(doorway)
    safe["doorway_title"] = doorway["title"]
    safe["doorway_url"] = doorway["url"]
    safe["doorway_rationale"] = doorway["rationale"]
    safe.pop("doorway_omission_exception_reason", None)
    safe["answer_basis"] = {
        "kind": "general_knowledge",
        "label": "General knowledge",
        "explanation": (
            "The conceptual distinction is a general-knowledge explanation. "
            "The separately linked Living Archive page is a related continuation, "
            "not a claim that the page is the source of every statement above."
        ),
    }
    safe["response_provenance"] = {
        "class": "deterministic_by_design",
        "provider": "bounded_complicated_complex_conceptual_contract",
        "model": None,
        "quality_adjusted_llm_eligible": False,
        "llm_invoked": False,
    }
    safe["provider"] = None
    safe["model"] = None
    safe["evidence"] = []
    safe["evidence_validation"] = {
        "version": "1.0",
        "status": "not_applicable",
        "reason": "general_knowledge_conceptual_recovery_not_source_attributed",
        "reference_count": 0,
        "claim_support": {
            "status": "not_applicable",
            "reason": "bounded_general_knowledge_conceptual_explanation",
            "semantic_certification": False,
        },
        "temporal_validity": {
            "status": "not_applicable",
            "reason": "no_temporal_claims_in_response",
        },
        "semantic_certification": False,
    }
    safe["processing"] = "final_visitor_boundary_complicated_complex_distinction"
    safe["route_source"] = "guide_final_visitor_boundary"
    safe["visitor_boundary_version"] = safe.get("visitor_boundary_version") or "shared-conceptual-contract"
    return safe
