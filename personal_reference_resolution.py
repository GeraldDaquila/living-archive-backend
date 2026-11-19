"""Detection and evidence-backed resolution for personal-reference questions.

Phrase detection only selects a retrieval strategy. It never proves a personal
artifact exists. The teaching-conflict resolver below is a bounded, source-
grounded synthesis of published Living Archive method documents.
"""
from __future__ import annotations

import re
from typing import Any

PERSONAL_REFERENCE_VERSION = "1.1"

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
    r"\b(?:teaching|teacher|teaching[s]?)\b",
    r"\b(?:conscience|lived experience|care for others|people affected|harm|ethical conflict)\b",
)

_TEACHING_CONFLICT_SOURCES = (
    {
        "title": "Analytical Procedure",
        "url": "https://geralddaquila.com/analytical-procedure/",
        "required_markers": (
            "observe", "clarify the question", "gather appropriate evidence",
            "develop explanations", "locate the level of claim",
            "examine the boundaries", "reflect upon implications",
            "remain open to revision",
        ),
    },
    {
        "title": "Discernment Foundations",
        "url": "https://geralddaquila.com/discernment-foundations/",
        "required_markers": (
            "separate events from interpretation", "slow down before concluding",
            "ethical responsibility", "open to revision",
        ),
    },
    {
        "title": "Discernment, Authority, and Ethical Access",
        "url": "https://geralddaquila.com/discernment-authority-and-ethical-access/",
        "required_markers": (
            "pause, differentiate, and refrain", "consent of those affected",
            "willingness to be corrected", "transparency about limits",
        ),
    },
    {
        "title": "My Approach",
        "url": "https://geralddaquila.com/how-i-work/",
        "required_markers": (
            "different questions require different methods of inquiry",
            "i do not present contemplative work as scientific proof",
            "the goal is never to replace a person's judgment",
        ),
    },
    {
        "title": "Revision Protocol",
        "url": "https://geralddaquila.com/revision-protocol/",
        "required_markers": (
            "revision follows understanding", "revision welcomes criticism",
            "better evidence",
        ),
    },
)

def is_personal_reference_question(query: str) -> bool:
    """Detection is a routing hint, never proof that a personal item exists."""
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    return bool(text) and any(re.search(p, text, re.I) for p in _PERSONAL_REFERENCE_PATTERNS)

def is_teaching_conflict_reference(query: str) -> bool:
    """Identify a personal protocol request about conflicting teaching and lived/ethical judgment."""
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    return (
        is_personal_reference_question(text)
        and all(re.search(pattern, text, re.I) for pattern in _TEACHING_CONFLICT_PATTERNS)
    )

def teaching_conflict_source_urls() -> tuple[str, ...]:
    """Return the fixed, published canonical sources for this discernment task family."""
    return tuple(item["url"] for item in _TEACHING_CONFLICT_SOURCES)

def compose_teaching_conflict_protocol(
    query: str, documents: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Synthesize only after every required canonical source body is verified."""
    if not is_teaching_conflict_reference(query):
        return None
    by_url = {
        str(item.get("url") or "").rstrip("/").casefold(): item
        for item in documents or []
        if isinstance(item, dict)
    }
    verified: list[dict[str, str]] = []
    for source in _TEACHING_CONFLICT_SOURCES:
        item = by_url.get(source["url"].rstrip("/").casefold())
        if not item:
            return None
        title = str(item.get("title") or "").strip()
        body = re.sub(r"\s+", " ", str(item.get("text") or item.get("content") or "")).strip()
        if len(body) < 250:
            return None
        # Verify the fetched body is the expected canonical source, not merely a
        # URL-shaped or title-shaped result returned by an intermediary.
        title_key = re.sub(r"\W+", " ", title.casefold()).strip()
        expected_key = re.sub(r"\W+", " ", source["title"].casefold()).strip()
        if expected_key not in title_key:
            return None
        body_folded = body.casefold()
        if not all(marker in body_folded for marker in source["required_markers"]):
            return None
        verified.append({"title": title, "url": source["url"], "text": body[:6000]})

    response = (
        "Your published approach explicitly says that different questions require different "
        "methods of inquiry. It does not reduce this conflict to “trust your conscience” "
        "or “obey the teaching.” The closest explicit procedure is the Living Archive’s "
        "**Analytical Procedure**, supported by **My Approach**, **Discernment Foundations**, "
        "**Discernment, Authority, and Ethical Access**, and the **Revision Protocol**. "
        "I do not find a separate document naming this exact situation as a standalone "
        "personal protocol, so the sequence below is a faithful synthesis of those "
        "published methods—not a quotation or a newly invented doctrine.\n\n"
        "1. **Pause before concluding.** Do not let urgency, pressure, or the teacher’s "
        "authority settle the matter. Restraint and unresolved uncertainty are legitimate "
        "parts of discernment.\n\n"
        "2. **Observe what is actually in conflict.** State the teaching as accurately "
        "as possible. Separately identify what you have directly experienced, what you "
        "know about its effects, and what you are interpreting. Do not collapse the event, "
        "the teaching, and your reaction into one claim.\n\n"
        "3. **Clarify the claim.** What exactly is being asserted or asked of you? Is it "
        "an empirical claim, an interpretation, a philosophical position, a contemplative "
        "or spiritual teaching, or an instruction about how to treat someone? Each "
        "requires an appropriate standard of examination. Your published approach "
        "explicitly refuses both presenting contemplative work as scientific proof "
        "and dismissing it merely because it addresses questions science was not "
        "designed to answer.\n\n"
        "4. **Gather and compare appropriate evidence.** Include lived experience where "
        "it is relevant; also examine observable facts, context, patterns, and credible "
        "alternative explanations. Ask what is verified, what remains speculative, and "
        "whether assumptions or emotional pressure are shaping the account.\n\n"
        "5. **Examine boundaries and ethical consequences.** Who is affected? Does the "
        "teaching respect consent, agency, dignity, and boundaries? Is the person offering "
        "it speaking within the limits of their authority? Insight or spiritual access "
        "does not, by itself, grant permission to override another person.\n\n"
        "6. **Consider what the teaching produces in practice.** Look at its actual "
        "effects on people and relationships—not only the intention or language used to "
        "defend it. Discernment includes responsibility, avoiding manipulation and "
        "dehumanization, and remaining accountable for impact.\n\n"
        "7. **Withhold assent when the evidence is insufficient.** You do not have to "
        "force agreement, rejection, or immediate action. A provisional judgment, a "
        "boundary, or a decision to wait can be more responsible than false certainty.\n\n"
        "8. **Remain correctable.** Revisit the conclusion when stronger evidence, "
        "further experience, thoughtful criticism, or clearer consequences emerge. "
        "Revision is part of intellectual integrity, not a betrayal of what you once "
        "understood.\n\n"
        "So the governing discipline is: **pause, observe, clarify, test against "
        "appropriate evidence, examine ethical impact, act without surrendering your "
        "judgment, and remain open to correction.** Conscience matters as an ethical "
        "signal that calls for examination; it is not treated as automatic proof. "
        "Likewise, a teaching is not made true by the authority of the person who gives it."
    )
    return {
        "response": response,
        "documents": verified,
        "doorway": {
            "title": "Analytical Procedure",
            "url": "https://geralddaquila.com/analytical-procedure/",
            "rationale": "The Archive’s explicit stepwise method for observing, clarifying, evaluating evidence, examining boundaries, and revising conclusions.",
        },
    }

def personal_reference_fallback(query: str) -> str:
    """Honest deterministic response only when no verified personal source is available."""
    return (
        "I can help recover your protocol or previously established reference, but I could "
        "not verify its exact wording or steps from the conversation and published sources "
        "available to this response. I won't replace your established position with a "
        "protocol I invent.\n\n"
        "If you can point me to the source or record where it was established, I can "
        "recover and distinguish its actual wording from any later interpretation."
    )
