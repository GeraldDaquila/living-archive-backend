"""Answer-first conceptual distinction contract for event, pattern, and system structure.

This bounded final visitor contract repairs a specific failure mode: a question
restatement or navigation handoff must never substitute for the requested
conceptual explanation. It runs after exact Gold Star authority and before the
final visitor payload is returned.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.1"


def is_event_pattern_structure_question(query: str) -> bool:
    q = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    asks_distinction_or_definition = bool(re.search(
        r"\b(?:difference|distinguish|distinction|differentiate|compare|"
        r"relationship|relate|interact|become|define|definition|mean|means)\b",
        q,
    )) or bool(re.search(r"\bwhat\s+(?:is|are)\b", q))
    names_event = bool(re.search(r"\bevents?\b", q))
    names_pattern = bool(re.search(r"\bpatterns?\b", q))
    names_structure = bool(re.search(
        r"\b(?:system\s+structures?|structures?\s+of\s+(?:a\s+)?systems?)\b",
        q,
    ))
    return asks_distinction_or_definition and names_event and names_pattern and names_structure


def has_event_pattern_structure_explanation(response: str) -> bool:
    text = re.sub(r"\s+", " ", str(response or "").casefold())
    has_event = bool(
        re.search(r"\bevent\b", text)
        and re.search(r"\b(?:single|particular|one-off|one-time|occurrence|happens|isolated)\b", text)
    )
    has_pattern = bool(
        re.search(r"\bpattern\b", text)
        and re.search(r"\b(?:repeated|recurring|over time|repeatedly|developing sequence)\b", text)
    )
    has_structure = bool(
        re.search(r"\bsystem structure\b", text)
        and re.search(r"\b(?:relationships|rules|incentives|arrangements|conditions|dependencies)\b", text)
    )
    causal = bool(re.search(
        r"\b(?:produce|shape|generate|sustain|reproduce|underlie|influence|"
        r"make more likely|contribute to)\w*\b",
        text,
    ))
    example = bool(re.search(r"\b(?:for example|for instance|imagine)\b", text))
    return has_event and has_pattern and has_structure and causal and example


def event_pattern_structure_recovery() -> str:
    return (
        "An **event** is a particular thing that happens: one resignation, one service failure, or one missed deadline. "
        "A **pattern** is a recurring or developing sequence of events that becomes visible over time, such as repeated resignations or repeated service failures. "
        "A **system structure** is the underlying arrangement of relationships, rules, incentives, resources, information flows, and dependencies that shapes which patterns are likely to occur and persist.\n\n"
        "For example, one employee leaving is an event. Several employees leaving the same team over successive months may reveal a pattern. The structure might include an unmanageable workload, unclear authority, poor feedback channels, or incentives that reward output while ignoring the cost to staff. Those conditions can help produce the pattern; they are not proved by the pattern alone. Other explanations may also need to be examined.\n\n"
        "The distinction matters because each level calls for a different response. An event may need immediate attention; a pattern calls for looking across multiple occurrences; and understanding the structure means examining and, where justified, changing the conditions that keep generating the pattern. The aim is not to ignore individual events, but to avoid repeatedly treating symptoms while leaving their possible causes untouched."
    )


def _mark_deterministic_recovery(safe: dict[str, Any]) -> None:
    prior_provider = safe.get("provider")
    prior_model = safe.get("model")
    safe["provider"] = None
    safe["model"] = None
    safe["response_provenance"] = {
        "class": "deterministic_recovery",
        "provider": "bounded_event_pattern_structure_answer_first",
        "model": None,
        "quality_adjusted_llm_eligible": False,
        "llm_invoked": bool(prior_provider or prior_model),
        "prior_generation_present": bool(prior_provider or prior_model),
    }
    safe["evidence"] = []
    safe["evidence_validation"] = {
        "version": "1.0",
        "status": "not_applicable",
        "reason": "bounded_general_knowledge_recovery_not_attributed_to_retrieved_sources",
        "reference_count": 0,
        "claim_support": {
            "status": "not_applicable",
            "reason": "general_conceptual_explanation",
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


def apply_event_pattern_structure_boundary(query: str, payload: Any) -> Any:
    if not isinstance(payload, dict) or not is_event_pattern_structure_question(query):
        return payload
    safe = dict(payload)
    response = str(safe.get("response") or safe.get("answer") or "")
    if has_event_pattern_structure_explanation(response):
        return safe

    recovered = event_pattern_structure_recovery()
    safe["response"] = recovered
    if "answer" in safe:
        safe["answer"] = recovered
    safe["response_shape"] = "conceptual_distinction"
    safe["processing"] = "final_visitor_boundary_event_pattern_structure_answer_first"
    safe["route_source"] = "guide_final_visitor_boundary"
    safe["answer_basis"] = {
        "kind": "general_knowledge",
        "label": "General conceptual explanation",
        "explanation": (
            "This distinction is explained from general systems-thinking knowledge; "
            "the separately selected Archive destination is an application continuation, "
            "not evidence for the definitions."
        ),
    }
    safe["event_pattern_structure_contract"] = {
        "version": VERSION,
        "answer_first_enforced": True,
        "concepts_covered": ["event", "pattern", "system_structure"],
        "causal_claim_calibrated": True,
        "navigation_is_separate": True,
    }
    _mark_deterministic_recovery(safe)
    return safe
