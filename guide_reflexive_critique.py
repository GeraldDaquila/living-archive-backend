"""Bounded reflexive critique recognition and retrieval planning."""
from __future__ import annotations
import re
from typing import Any

VERSION = "1.0"
_ARCHIVE = (r"\b(?:the\s+)?(?:living\s+)?archive(?:'s|’s)?\b", r"\b(?:this\s+)?archive(?:'s|’s)?\b")
_CRITIQUE = (r"\bgood[- ]faith\s+critique\b", r"\bcritique\b", r"\bcritically\s+(?:examine|assess|evaluate|interrogate)\b", r"\b(?:challenge|test|scrutinize|scrutinise)\b", r"\bstrengths?\s+and\s+weaknesses\b", r"\blimitations?\b")
_WORLDVIEW = (r"\bworldviews?\b", r"\b(?:epistemolog(?:y|ical)|ontolog(?:y|ical))\b", r"\bunderlying\s+assumptions?\b", r"\bphilosoph(?:y|ical)\s+foundations?\b", r"\bcore\s+assumptions?\b")
_DIMENSIONS = ["reconstruct_the_archive_position_fairly", "clarify_definitions_and_hidden_assumptions", "separate_empirical_interpretive_and_normative_claims", "assess_provenance_evidence_and_independent_corroboration", "test_falsifiability_revisability_and_counterexamples", "examine_internal_coherence_and_external_validity", "consider_cultural_historical_and_power_effects", "identify_exclusions_and_unintended_consequences", "state_what_evidence_would_change_the_assessment"]

def build_reflexive_critique_plan(query: str) -> dict[str, Any] | None:
    raw = re.sub(r"\s+", " ", str(query or "")).strip()
    if not raw: return None
    if not (any(re.search(p, raw, re.I) for p in _ARCHIVE) and any(re.search(p, raw, re.I) for p in _CRITIQUE) and any(re.search(p, raw, re.I) for p in _WORLDVIEW)):
        return None
    retrieval_query = ("Living Archive stated worldview and philosophical foundations; underlying assumptions, ontology, epistemology, definitions, and normative commitments; evidence and provenance for empirical claims; independent corroboration and counterevidence; falsifiability, revisability, internal coherence, external validity, cultural and historical contingency, power effects, exclusions, unintended consequences, and limitations. Retrieve canonical published source bodies that state the Archive's own position and relevant sources that permit critical examination. Do not treat Archive publications as independent validation of their claims.")
    return {"version": VERSION, "mode": "reflexive_institutional_critique", "retrieval_query": retrieval_query, "evaluation_dimensions": list(_DIMENSIONS), "original_query_preserved": True, "doorway_authority": "unchanged_existing_canonical_gates"}

__all__ = ["VERSION", "build_reflexive_critique_plan"]
