"""Shared visitor-answer contract for humility and spiritual-maturity questions.

This contract is a bounded quality check, not a claim that spiritual maturity
can be objectively certified. It checks whether an answer addresses the
visitor's stated relationship question with the required distinctions.
"""
from __future__ import annotations

import re
from typing import Any

from gold_star_semantic_contract import remove_question_echo


def is_humility_spiritual_maturity_question(query: str) -> bool:
    question = re.sub(r"\s+", " ", str(query or "")).strip().casefold()
    return bool(
        re.search(r"\bhumility\b", question)
        and re.search(r"\bspiritual maturit(?:y|ies)\b", question)
        and re.search(
            r"\b(?:relationship|relation|connection|interplay|between|how do|how does|relate)\b",
            question,
        )
    )


def evaluate_humility_spiritual_maturity_response(query: str, answer: str) -> dict[str, Any]:
    """Return the same explicit answer checks used by provider admission and live QA."""
    if not is_humility_spiritual_maturity_question(query):
        return {"applies": False, "passed": True, "checks": {}}
    low = re.sub(
        r"\s+", " ",
        remove_question_echo(str(query or ""), str(answer or "")).casefold(),
    ).strip()
    humility_present = "humility" in low
    maturity_present = bool(re.search(r"\bspiritual maturit(?:y|ies)\b", low))
    learning_mechanism = (
        any(term in low for term in ("learning", "willing to learn", "remain teachable", "teachability"))
        and any(term in low for term in (
            "honest self-appraisal", "honest self-examination", "self-awareness",
            "recognize our limits", "recognising our limits", "recognizing our limits",
            "see ourselves clearly",
        ))
        and any(term in low for term in (
            "correction", "accept correction", "being corrected", "accountability",
            "openness to others", "open to others",
        ))
    )
    lived_maturity = any(term in low for term in (
        "lived conduct", "lived experience", "how a person lives", "how people live",
        "daily conduct", "actions and relationships", "ordinary conduct",
        "responsible action", "responsibility in relationships",
    ))
    rejects_self_erasure = (
        any(term in low for term in (
            "self-erasure", "self erasure", "diminished self-worth", "self-contempt",
            "not self-abandonment", "not self-abasing",
        ))
        or bool(re.search(
            r"\\b(?:not|is not|isn't|does not mean|doesn't mean|does not require|"
            r"doesn't require|rather than|instead of|different from|distinct from)\\b"
            r"[^.!?;]{0,160}\\b(?:self-negation|self negation|self-abasement|self abasement|"
            r"self-abandonment|self abandonment|loss of self-respect|lack of self-respect|"
            r"denial of (?:one's|their|your) worth|erasing oneself|erasing yourself|"
            r"abandoning self-respect)\\b",
            low,
        ))
    )
    preserves_boundaries = any(term in low for term in (
        "appropriate boundaries", "healthy boundaries", "personal boundaries",
        "does not mean surrendering boundaries", "doesn't mean surrendering boundaries",
    ))
    rejects_automatic_compliance = (
        any(term in low for term in (
            "not passivity", "not passive", "not automatic compliance",
            "not unquestioning compliance", "not blind obedience",
        ))
        or bool(re.search(
            r"\b(?:humility|it|this)\s+(?:is not|isn't|does not mean|doesn't mean|"
            r"does not entail|doesn't entail|is different from|differs from|"
            r"is distinct from|is not synonymous with|is not equivalent to)\b"
            r"[^.!?;]{0,180}\b(?:passivity|passive|blind obedience|automatic compliance)\b",
            low,
        ))
        or bool(re.search(
            r"\b(?:rather than|instead of|as opposed to|distinct from|different from|"
            r"not synonymous with|not equivalent to)\b"
            r"[^.!?;]{0,100}\b(?:passivity|passive|being passive|blind obedience|automatic compliance)\b",
            low,
        ))
        or bool(re.search(
            r"\bwithout\s+(?:becoming|requiring|implying|entailing)\b"
            r"[^.!?;]{0,100}\b(?:passivity|passive|being passive|blind obedience|automatic compliance)\b",
            low,
        ))
    )
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", low)
        if sentence.strip()
    ]
    mechanism_cue = re.compile(
        r"\b(?:allows?|enables?|supports?|shapes?|cultivates?|develops?|"
        r"strengthens?|depends on|requires?|makes it possible|reinforces?|influences?)\b",
        re.I,
    )
    relationship_mechanism = any(
        "humility" in sentence
        and bool(re.search(r"\bspiritual maturit(?:y|ies)\b", sentence))
        and bool(mechanism_cue.search(sentence))
        for sentence in sentences
    )
    relationship_direction_or_boundary = bool(re.search(
        r"\b(?:both|reciprocal|mutual|in turn|one another|each other|"
        r"not automatic|not necessarily|conditional|while|although|yet)\b",
        low,
    ))
    no_guarantee = any(term in low for term in (
        "does not guarantee", "doesn't guarantee", "not guarantee",
        "not automatically", "not by itself", "not sufficient by itself",
        "humility alone cannot", "humility alone does not",
    ))
    checks = {
        "names_both_concepts": humility_present and maturity_present,
        "relationship_mechanism": relationship_mechanism,
        "relationship_direction_or_boundary": relationship_direction_or_boundary,
        "humility_supports_learning_and_correction": learning_mechanism,
        "maturity_as_lived_conduct": lived_maturity,
        "not_self_erasure_or_self_contempt": rejects_self_erasure,
        "preserves_appropriate_boundaries": preserves_boundaries,
        "not_passivity_or_automatic_compliance": rejects_automatic_compliance,
        "does_not_guarantee_maturity": no_guarantee,
    }
    return {
        "applies": True,
        "passed": all(checks.values()),
        "checks": checks,
        "missing": [name for name, passed in checks.items() if not passed],
    }
