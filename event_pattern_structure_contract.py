"""Answer-first conceptual distinction contract for event, pattern, and system structure.

This is a shared final-response boundary: a navigation handoff cannot substitute
for the conceptual explanation requested by the visitor.
"""
from __future__ import annotations

import re
from typing import Any, Dict

VERSION = "1.0"

def is_event_pattern_structure_question(query: str) -> bool:
    q = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    asks_distinction = bool(re.search(r"\b(?:difference|distinguish|distinction|differentiate|compare)\b", q))
    names_event = bool(re.search(r"\bevents?\b", q))
    names_pattern = bool(re.search(r"\bpatterns?\b", q))
    names_structure = bool(re.search(r"\b(?:system\s+structures?|structures?\s+of\s+(?:a\s+)?systems?)\b", q))
    return asks_distinction and names_event and names_pattern and names_structure

def has_event_pattern_structure_explanation(response: str) -> bool:
    text = re.sub(r"\s+", " ", str(response or "").casefold())
    has_event = bool(re.search(r"\bevent\b", text) and re.search(r"\b(?:single|particular|one-off|occurrence|happens)\b", text))
    has_pattern = bool(re.search(r"\bpattern\b", text) and re.search(r"\b(?:repeated|recurring|over time|repeatedly)\b", text))
    has_structure = bool(re.search(r"\bsystem structure\b", text) and re.search(r"\b(?:relationships|rules|incentives|arrangements|conditions|dependencies)\b", text))
    causal = bool(re.search(r"\b(?:produce|shape|generate|sustain|reproduce|underlie)\w*\b", text))
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
        "explanation": "This distinction is explained from general systems-thinking knowledge; the separate Archive destination is a continuation for application, not evidence for the definitions."
    }
    safe["event_pattern_structure_contract"] = {
        "version": VERSION,
        "answer_first_enforced": True,
        "concepts_covered": ["event", "pattern", "system_structure"],
        "causal_claim_calibrated": True,
        "navigation_is_separate": True,
    }
    return safe
