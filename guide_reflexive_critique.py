"""First-class answer planning for reflexive institutional critique."""
from __future__ import annotations

import re
from typing import Any

VERSION = "3.0"
_ARCHIVE = (
    r"\b(?:the\s+)?(?:living\s+)?archive(?:'s|’s)?\b",
    r"\b(?:this\s+)?archive(?:'s|’s)?\b",
)
_CRITIQUE = (
    r"\bgood[- ]faith\s+critique\b", r"\bcritique\b",
    r"\bcritically\s+(?:examine|assess|evaluate|interrogate)\b",
    r"\b(?:challenge|test|scrutinize|scrutinise)\b",
    r"\bstrengths?\s+and\s+weaknesses\b", r"\blimitations?\b",
)
_WORLDVIEW = (
    r"\bworldviews?\b", r"\b(?:epistemolog(?:y|ical)|ontolog(?:y|ical))\b",
    r"\bunderlying\s+assumptions?\b", r"\bphilosoph(?:y|ical)\s+foundations?\b",
    r"\bcore\s+assumptions?\b",
)
_DIMENSIONS = [
    "reconstruct_the_archive_position_fairly",
    "clarify_definitions_and_hidden_assumptions",
    "separate_empirical_interpretive_and_normative_claims",
    "assess_provenance_evidence_and_independent_corroboration",
    "test_falsifiability_revisability_and_counterexamples",
    "examine_internal_coherence_and_external_validity",
    "consider_cultural_historical_and_power_effects",
    "identify_exclusions_and_unintended_consequences",
    "state_what_evidence_would_change_the_assessment",
]
_ANSWER_REQUIREMENTS = [
    "define_good_faith_critique_in_direct_answer_to_the_visitor",
    "explain_operational_tests_not_merely_list_topics",
    "reconstruct_the_archive_claim_before_evaluating_it",
    "separate_descriptive_empirical_normative_and_metaphysical_claims",
    "test_internal_coherence_and_external_evidence_independently",
    "include_the_strongest_fair_objection_and_a_fair_reply",
    "identify_counterexamples_and_evidence_that_would_change_the_judgment",
    "apply_to_archive_claims_only_when_substantive_sources_support_them",
    "never_treat_archive_self_description_as_independent_validation",
    "when_archive_sources_are_missing_answer_the_methodological_question_anyway",
    "never_replace_the_answer_with_a_resource_summary_or_retrieval_apology",
    "offer_no_doorway_unless_existing_canonical_authority_and_relevance_gates_pass",
]


def build_reflexive_critique_plan(query: str) -> dict[str, Any] | None:
    raw = re.sub(r"\s+", " ", str(query or "")).strip()
    if not raw or not (
        any(re.search(p, raw, re.I) for p in _ARCHIVE)
        and any(re.search(p, raw, re.I) for p in _CRITIQUE)
        and any(re.search(p, raw, re.I) for p in _WORLDVIEW)
    ):
        return None

    retrieval_query = (
        "Retrieve substantive canonical passages stating the Living Archive's own "
        "foundational worldview claims: its purpose as sensemaking infrastructure; "
        "its account of human development; ontology and epistemology; complexity "
        "and uncertainty; knowledge and evidence; agency and interdependence; systems; "
        "stewardship and responsibility; and human change. Prefer direct definitions, "
        "principles, assumptions, qualifications, limits, and constitutional or "
        "constitutional or cornerstone texts and source passages. Exclude WordPress media records, image captions, "
        "header or featured-image metadata, attachment descriptions, alt text, URLs, "
        "navigation labels, site boilerplate, and markup fragments. Exclude unrelated "
        "applied examples about commons contributions, resource sharing, or group "
        "fairness unless they directly explain a foundational worldview claim. "
        "The visitor asks for a good-faith critique: retrieval reconstructs what the "
        "Archive actually claims; it does not supply or replace the methodological "
        "answer. Archive self-description is evidence of what it says, not independent "
        "proof that it is true."
    )
    return {
        "version": VERSION,
        "mode": "reflexive_institutional_critique",
        "task_class": "answer_first_critical_evaluation",
        "retrieval_query": retrieval_query,
        "evaluation_dimensions": list(_DIMENSIONS),
        "answer_requirements": list(_ANSWER_REQUIREMENTS),
        "response_contract": {
            "primary_deliverable": (
                "A direct, self-contained method for evaluating the Archive in good faith, "
                "with a bounded application to its claims where substantive evidence exists."
            ),
            "required_sequence": [
                "define_good_faith_critique",
                "reconstruct_claims_fairly",
                "test_definitions_and_assumptions",
                "evaluate_evidence_and_counterexamples",
                "assess_coherence_scope_and_consequences",
                "state_revision_conditions",
            ],
            "retrieval_role": "evidence_for_application_not_a_substitute_for_the_answer",
            "fallback": (
                "answer_the_general_methodological_question_and_bound_archive_specific_claims"
            ),
            "forbidden_substitutes": [
                "resource_catalogue_summary",
                "retrieval_apology_as_the_answer",
                "wordpress_media_or_image_metadata",
                "unsupported_claims_about_archive_doctrine",
            ],
            "doorway_policy": "existing_canonical_authority_and_relevance_gates_only",
        },
        "original_query_preserved": True,
        "doorway_authority": "unchanged_existing_canonical_gates",
    }


__all__ = ["VERSION", "build_reflexive_critique_plan"]
