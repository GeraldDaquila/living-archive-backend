"""Provider-independent answer recovery for exhausted Guide request paths.

This module owns bounded answer content and its provenance disclosure only.
Canonical navigation is selected independently by the shared visitor boundary;
a related doorway must never be represented as evidence for the recovery answer.
"""
from __future__ import annotations

import re


def compose_visitor_failure_recovery(query: str) -> dict[str, str]:
    """Return a non-empty, provenance-limited visitor response after hard failure."""
    question = re.sub(r"\s+", " ", str(query or "")).strip()
    normalized = question.casefold()

    if (
        re.search(r"\btransform(?:ation|ing|ed)?\b", normalized)
        and re.search(r"\brebrand(?:ing|ed)?\b", normalized)
    ):
        response = (
            "Transformation becomes mere rebranding when the language, identity, "
            "structure, or promises change while the system's underlying behaviour "
            "remains materially the same. The test is not whether new names or "
            "strategies appear, but whether decision rights, incentives, resource "
            "flows, accountability, everyday practices, and outcomes change. "
            "If the same people retain the same power, the same costs are pushed "
            "onto others, and the same behaviours continue to be rewarded, the "
            "change is largely cosmetic. Genuine transformation produces durable, "
            "observable differences in how the system works and how people "
            "experience it—and makes those differences open to scrutiny and "
            "correction.\n\n"
            "This is a bounded general-knowledge orientation because the Guide's "
            "live answer and canonical-retrieval services were unavailable on this "
            "attempt. It is not presented as a synthesis of verified Living Archive "
            "sources. Any separately selected Archive resource is a related "
            "continuation, not evidence for this answer."
        )
        basis = (
            "A provider-independent conceptual orientation. Live generation and "
            "canonical retrieval were unavailable, so no Living Archive source "
            "attribution is claimed. The shared visitor boundary may independently "
            "select a verified, relevant Archive continuation; that destination "
            "does not substantiate this general-knowledge answer."
        )
        return {"response": response, "basis_explanation": basis}

    response = (
        "I couldn't complete the full answer or verify a relevant Living Archive "
        "source on this attempt. I don't want to invent an Archive-backed answer "
        "or send you to an unverified page. Your question is still intact. A useful "
        "way to continue is to identify the part that matters most: the change you "
        "are observing, the people affected by it, or the evidence that would show "
        "whether the change is real and durable. You can continue from that point "
        "without having to reconstruct the original question.\n\n"
        "This is a service-limited recovery message, not a substantive answer or "
        "a claim that the Living Archive has been searched successfully."
    )
    basis = (
        "Service-limited recovery message. The Guide could not complete generation "
        "or verify Living Archive canonical sources, so no substantive answer or "
        "Living Archive attribution is claimed."
    )
    return {"response": response, "basis_explanation": basis}
