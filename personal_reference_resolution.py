"""Personal-reference detection and question-family composition.

Source identity and body verification are delegated to the shared evidence
contract. Question-specific language is kept separate from site-wide source
integrity rules.
"""
from __future__ import annotations

import re
from typing import Any

from source_evidence_contract import resolve_source_documents

PERSONAL_REFERENCE_VERSION = "1.2"

_PERSONAL_ARTIFACT = (
    r"(?:protocol|framework|approach|method|practice|principle|position|"
    r"decision|agreement|standard|rule|criteria|plan|commitment|teaching|"
    r"belief|view|preference|instruction|understanding)"
)
_PERSONAL_REFERENCE_PATTERNS = (
    rf"\b(?:my|our|the one we|what we)\b.{{0,100}}\b{_PERSONAL_ARTIFACT}\b",
    r"\bwhat (?:did i|have i|did we|have we) (?:say|decide|agree|establish|settle|define)",
    r"\bwhat was (?:my|our) (?:position|decision|agreement|approach|protocol|framework)",
    r"\b(?:as i said|as we agreed|what i previously said|what we previously agreed)\b",
)

_TEACHING_CONFLICT_PATTERNS = (
    r"\b(?:teaching|teacher|teachings)\b",
    r"\b(?:conscience|lived experience|care for others|people affected|harm|ethical conflict)\b",
)

# This is a question-family candidate list, not the site-wide source registry.
# Core sources are required for this particular synthesis; the remaining sources
# strengthen it when available but do not make the entire answer fail closed.
_TEACHING_CONFLICT_SOURCES = (
    {
        "title": "Analytical Procedure",
        "url": "https://geralddaquila.com/analytical-procedure/",
        "role": "core",
    },
    {
        "title": "Discernment Foundations",
        "url": "https://geralddaquila.com/discernment-foundations/",
        "role": "core",
    },
    {
        "title": "Discernment, Authority, and Ethical Access",
        "url": "https://geralddaquila.com/discernment-authority-and-ethical-access/",
        "role": "core",
    },
    {
        "title": "My Approach",
        "url": "https://geralddaquila.com/how-i-work/",
        "role": "supporting",
    },
    {
        "title": "Revision Protocol",
        "url": "https://geralddaquila.com/revision-protocol/",
        "role": "supporting",
    },
)


def is_personal_reference_question(query: str) -> bool:
    """Detection is a routing hint, never proof that a personal item exists."""
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    return bool(text) and any(re.search(p, text, re.I) for p in _PERSONAL_REFERENCE_PATTERNS)


def is_teaching_conflict_reference(query: str) -> bool:
    """Identify a personal protocol request about teaching and ethical judgment."""
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    return (
        is_personal_reference_question(text)
        and all(re.search(pattern, text, re.I) for pattern in _TEACHING_CONFLICT_PATTERNS)
    )


def teaching_conflict_source_urls() -> tuple[str, ...]:
    """Return bounded canonical source candidates for this question family."""
    return tuple(item["url"] for item in _TEACHING_CONFLICT_SOURCES)


def compose_teaching_conflict_protocol(
    query: str, documents: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Compose a qualified synthesis from verified core sources.

    Optional supporting sources are included when verified. A missing optional
    source does not erase otherwise sufficient evidence. The result never claims
    that the bounded source set exhausts the Archive or private conversation.
    """
    if not is_teaching_conflict_reference(query):
        return None

    expected = list(_TEACHING_CONFLICT_SOURCES)
    resolution = resolve_source_documents(
        expected,
        documents or [],
        required_titles=(
            "Analytical Procedure",
            "Discernment Foundations",
            "Discernment, Authority, and Ethical Access",
        ),
        min_verified=3,
        min_body_chars=250,
    )
    if not resolution.get("verified"):
        return None

    verified = resolution["verified_sources"]
    source_names = ", ".join(f"**{item['title']}**" for item in verified)
    response = (
        "I can recover a **source-grounded discernment synthesis** from the published "
        f"Living Archive methods: {source_names}. I cannot verify from this bounded "
        "source set that this is the exact wording of a separately established personal "
        "protocol, or that it exhausts anything recorded in private conversations or files. "
        "The following is a careful synthesis of the published sources, not a quotation "
        "or a claim that these exact steps were previously agreed.\n\n"
        "1. **Pause before concluding.** Do not let urgency, pressure, or a teacher’s "
        "authority settle the matter. Discernment includes the capacity to refrain and "
        "to leave uncertainty unresolved while you examine it.\n\n"
        "2. **Separate what happened from what it means.** State the teaching as "
        "accurately as possible. Distinguish what you directly experienced, what is "
        "observable or verified, what others report, and what you are interpreting.\n\n"
        "3. **Clarify the kind of claim being made.** Is it empirical, historical, "
        "philosophical, contemplative, spiritual, or an instruction about how someone "
        "should be treated? Different questions require appropriate methods and standards "
        "of evidence. Do not present contemplative claims as scientific proof, or dismiss "
        "them simply because they address a different kind of question.\n\n"
        "4. **Gather and compare appropriate evidence.** Include lived experience where "
        "it is relevant, alongside observable facts, context, patterns, and alternative "
        "explanations. Distinguish what is established from what remains speculative.\n\n"
        "5. **Examine authority, consent, and consequences.** Ask who is affected, whether "
        "their agency and boundaries are respected, and whether the teacher is accountable "
        "for impact and willing to be corrected. Insight or access does not itself confer "
        "ethical authority or permission to override another person.\n\n"
        "6. **Withhold assent or action when the grounds are insufficient.** You do not "
        "have to force agreement, rejection, or immediate action. Restraint, a boundary, "
        "or a provisional judgment may be more responsible than false certainty.\n\n"
        "7. **Remain open to revision.** Reconsider when stronger evidence, further "
        "experience, thoughtful criticism, or clearer consequences emerge. Revision "
        "serves understanding; it is not a betrayal of integrity.\n\n"
        "The governing discipline is therefore: **pause, observe, distinguish, clarify, "
        "test against appropriate evidence, examine ethical responsibility, and remain "
        "correctable.** Conscience deserves serious attention as an ethical signal, but "
        "it is not automatic proof. A teaching deserves examination, but a teacher’s "
        "authority is not proof of its truth."
    )
    return {
        "response": response,
        "documents": verified,
        "evidence_resolution": {
            "version": resolution["version"],
            "status": resolution["status"],
            "verified_count": resolution["verified_count"],
            "missing_sources": resolution["missing_sources"],
            "corpus_absence_proven": False,
        },
        "doorway": {
            "title": "Analytical Procedure",
            "url": "https://geralddaquila.com/analytical-procedure/",
            "rationale": (
                "The Archive’s explicit method for observing, clarifying, evaluating "
                "evidence, examining boundaries, and revising conclusions."
            ),
        },
    }


def personal_reference_fallback(query: str) -> str:
    """State the bounded retrieval limit without claiming global source absence."""
    return (
        "I can help recover an established reference, but I could not verify its exact "
        "wording in the conversation and source material available to this response. "
        "That is a limit of this retrieval, not proof that no such record exists. I will "
        "not invent or replace an established position.\n\n"
        "I can still identify relevant published material, distinguish a source-grounded "
        "interpretation from a recovered personal statement, and explain what remains "
        "unverified."
    )
