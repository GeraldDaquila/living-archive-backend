"""Claim-level provenance discipline for mixed quotation/paraphrase/interpretation answers.

This contract is deliberately narrow: it applies when a visitor asks how to
trace a passage that combines direct quotation, paraphrase, and interpretation.
It does not require citations in ordinary conceptual answers or manufacture
source locators that are absent from the supplied material.
"""
from __future__ import annotations

import re
from typing import Any, Dict

CONTRACT_VERSION = "v1"


def is_source_provenance_question(query: Any) -> bool:
    """Recognize questions about tracing all three epistemic layers."""
    text = " ".join(str(query or "").casefold().split())
    has_quote = bool(re.search(r"\b(?:quote|quotation|quoted)\b", text))
    has_paraphrase = bool(re.search(r"\bparaphras(?:e|ed|ing|is)\b", text))
    has_interpretation = bool(re.search(r"\b(?:interpretation|interpretive|inference)\b", text))
    asks_traceability = bool(re.search(
        r"\b(?:trace|traceable|traceability|provenance|attribute|attribution|source|verify)\w*\b",
        text,
    ))
    return has_quote and has_paraphrase and has_interpretation and asks_traceability


def build_source_provenance_instruction() -> str:
    """Return the reusable claim-level provenance instruction for this task."""
    return (
        "MIXED-SOURCE PROVENANCE — QUOTATION, PARAPHRASE, AND INTERPRETATION:\n"
        "Explain traceability at the smallest practical claim-bearing span, not merely by attaching one citation to a whole sentence. "
        "For a direct quotation, preserve the exact source wording and identify the source/work and a precise locator when the source provides one; "
        "mark omissions, insertions, and editorial emphasis transparently. For a paraphrase, use the Guide's own wording, cite the passage it restates, "
        "and preserve its scope, modality, uncertainty, conditions, and qualifications. A phrase such as 'in other words' is not attribution. "
        "For interpretation or synthesis, explicitly identify it as the Guide's inference, name the source-derived claims it builds on, and explain "
        "the inferential step; do not imply the source itself made the interpretation unless it did. When Q, P, and I are interwoven, mark their "
        "clauses/spans separately or split the sentence if the boundaries are unclear. A trailing citation must not appear to support a claim it does "
        "not establish. If the source text or locator is unavailable, disclose that limitation; never invent a quotation, page, section, paragraph, "
        "or other source metadata. Give the reader a path to independently verify each source-derived span and understand each Guide-generated inference. "
        "Do not force these labels or this structure into unrelated answers."
    )


def evaluate_source_provenance_response(query: Any, response: Any) -> Dict[str, Any]:
    """Check that a response explains all three layers and their boundary rules."""
    if not is_source_provenance_question(query):
        return {"applies": False, "passed": True, "missing": []}

    text = " ".join(str(response or "").casefold().split())
    checks = {
        "quotation_fidelity": bool(
            re.search(r"\b(?:exact|verbatim|original)\b.{0,100}\b(?:word|wording|quotation|quote)\b|"
                      r"\b(?:quotation|quote)\b.{0,100}\b(?:exact|verbatim|source)\b", text)
        ),
        "source_locator": bool(
            re.search(r"\b(?:source|author|work|document)\b", text)
            and re.search(r"\b(?:page|section|paragraph|chapter|timestamp|locator|location)\b", text)
        ),
        "paraphrase_fidelity": bool(
            re.search(r"\bparaphras\w*\b", text)
            and re.search(r"\b(?:own words|restat\w*|rephras\w*)\b", text)
            and re.search(r"\b(?:scope|qualification|qualifier|modality|condition|uncertainty)\w*\b", text)
        ),
        "interpretation_boundary": bool(
            re.search(r"\b(?:interpretation|interpretive|inference|analysis|synthesis)\b", text)
            and re.search(r"\b(?:guide's|guide’s|your own|own)\b.{0,80}\b(?:analysis|interpretation|inference|conclusion)\b|"
                          r"\b(?:label|identify|signal|distinguish)\w*\b.{0,100}\b(?:interpretation|inference)\b", text)
        ),
        "inferential_bridge": bool(
            re.search(r"\b(?:builds on|rests on|depends on|draws from|based on)\b", text)
            and re.search(r"\b(?:reasoning|inferential|inference|why|how)\b", text)
        ),
        "claim_level_separation": bool(
            re.search(r"\b(?:claim|clause|span)\w*\b", text)
            and re.search(r"\b(?:separat\w*|distinct|boundary|split)\b", text)
        ),
        "unavailable_source_disclosure": bool(
            re.search(r"\b(?:unavailable|cannot be verified|could not be verified|not available|not supplied)\b", text)
            and re.search(r"\b(?:source|locator|location|metadata)\b", text)
        ),
        "no_false_attribution": bool(
            re.search(r"\b(?:do not|don't|never|must not|should not)\b.{0,100}\b(?:attribute|imply|invent|fabricat|lend)\w*\b", text)
            or re.search(r"\bnot (?:the source's|the source’s|the author's|the author’s)\b", text)
        ),
    }
    missing = [name for name, passed in checks.items() if not passed]
    return {
        "applies": True,
        "passed": not missing,
        "missing": missing,
        "version": CONTRACT_VERSION,
    }
