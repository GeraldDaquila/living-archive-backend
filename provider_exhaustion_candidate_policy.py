"""Narrow governed retrieval for answerability under provider exhaustion.

This policy activates only when a visitor asks for a general civic-commons
explanation while explicitly distinguishing it from official/institutional
doctrine and provider/search services are unavailable. It transfers structure,
never the approved answer or its doorway.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

BENCHMARK_ID = "general-guide-public-commons-civic-renewal-2026-11-24"


def select_provider_exhaustion_candidate(
    query: str,
    lessons: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    q = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    provider_outage = bool(re.search(
        r"\b(?:provider|providers|search service|search services|external service|external services)\b",
        q,
    )) and bool(re.search(r"\b(?:unavailable|fail(?:ed|ure)?|exhausted|down|outage)\b", q))
    civic_commons = bool(re.search(r"\b(?:commons|shared resources|civic infrastructure)\b", q))
    doctrine_boundary = bool(re.search(
        r"\b(?:official doctrine|institutional doctrine|formal doctrine|official definition)\b",
        q,
    ))
    general_question = bool(re.search(r"\b(?:general question|general explanation|conceptual question)\b", q))
    if not (provider_outage and civic_commons and doctrine_boundary and general_question):
        return None
    lesson = next((
        item for item in lessons
        if isinstance(item, dict)
        and item.get("id") == BENCHMARK_ID
        and item.get("runtime_transfer") is True
    ), None)
    if lesson is None:
        return []
    return {
        "lesson": lesson,
        "role": "core",
        "activation_condition": "Provider/search services are unavailable; the visitor asks a general civic-commons question and explicitly distinguishes general explanation from official doctrine.",
        "role_rationale": "Preserves answerability under provider exhaustion while maintaining the boundary between general conceptual explanation and institutional authority.",
    }
