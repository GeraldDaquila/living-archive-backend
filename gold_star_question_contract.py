"""Versioned, source-independent contract for understanding visitor questions.

This module deliberately records conservative observations, not semantic
certification. Unknown and mixed-intent questions are valid outcomes. Runtime
routes may enrich the contract with verified domain knowledge, but must not
upgrade confidence from phrase matching alone.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from gold_star_semantic_contract import classify_question as _classify_question_candidate

from guide_reflexive_critique import build_reflexive_critique_plan

from personal_reference_resolution import (
    PERSONAL_REFERENCE_VERSION,
    is_personal_reference_question,
    is_teaching_conflict_reference,
)

VERSION = "1.2"

_NO_HANDOFF_PATTERNS = (
    r"\bdo not\b.{0,50}\b(?:recommend|suggest|link|refer|follow[- ]?up)\b",
    r"\bno\s+(?:links?|resources?|recommendations?|follow[- ]?ups?)\b",
    r"\bwithout\s+(?:any\s+)?(?:links?|resources?|recommendations?|follow[- ]?ups?)\b",
)
_NO_EXTERNAL_RESEARCH = (
    r"\bdo not\b.{0,50}\b(?:search|browse|use the web|look online)\b",
    r"\bno (?:web|internet) search\b",
)
_MULTI_INTENT_MARKERS = (
    r"\band\s+(?:also\s+)?(?:explain|compare|evaluate|recommend|draft|calculate|identify|analyze|analyse)\b",
    r"\bthen\s+(?:explain|compare|evaluate|recommend|draft|calculate|identify|analyze|analyse)\b",
    r"\b(?:first|secondly|additionally|in addition)\b",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.I | re.S) for pattern in patterns)


def _is_personal_stewardship_invitation(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", str(text or "").casefold()).strip()
    return bool(
        re.search(r"\bwho\s+or\s+what\s+is\s+(?:asking|calling|inviting|seeking)\b", normalized)
        and re.search(r"\b(?:responsible\s+care|stewardship|responsibility|care)\b", normalized)
        and re.search(r"\b(?:through|from|of|within)\s+me\b", normalized)
    )


def build_question_contract(query: str) -> Dict[str, Any]:
    """Build a conservative task contract without pretending to understand more than we do."""
    raw = str(query or "").strip()
    normalized = re.sub(r"\s+", " ", raw)
    no_handoff = _matches_any(normalized, _NO_HANDOFF_PATTERNS)
    no_external_research = _matches_any(normalized, _NO_EXTERNAL_RESEARCH)
    multi_intent = _matches_any(normalized, _MULTI_INTENT_MARKERS)
    reflexive_critique_plan = build_reflexive_critique_plan(normalized)
    # Reuse the runtime's canonical meta-coverage detector and structured
    # contract. Lazy import avoids a module-load dependency cycle.
    try:
        from deterministic_answer_recovery import (
            is_guide_meta_coverage_policy_question,
            build_guide_meta_coverage_policy_contract,
            is_epistemic_category_distinction_question,
            build_epistemic_category_distinction_contract,
        )
        meta_coverage_policy = is_guide_meta_coverage_policy_question(normalized)
        epistemic_category_distinction = is_epistemic_category_distinction_question(normalized)
        epistemic_distinction_contract = (
            build_epistemic_category_distinction_contract()
            if epistemic_category_distinction else None
        )
        meta_governance_contract = (
            build_guide_meta_coverage_policy_contract()
            if meta_coverage_policy else None
        )
    except Exception:
        meta_coverage_policy = False
        meta_governance_contract = None
        epistemic_category_distinction = False
        epistemic_distinction_contract = None

    task_candidate = (
        {"type": "guide_meta_coverage_policy"}
        if meta_coverage_policy
        else (
            {"type": "reflective_inquiry"}
            if _is_personal_stewardship_invitation(normalized)
            else (
                {"type": "institutional_critique"}
                if reflexive_critique_plan else _classify_question_candidate(normalized)
            )
        )
    )
    personal_reference = is_personal_reference_question(normalized)
    teaching_conflict_reference = is_teaching_conflict_reference(normalized)
    has_question = "?" in normalized or bool(
        re.match(r"^(?:who|what|when|where|why|how|which|can|could|should|would|is|are|does|do)\b", normalized, re.I)
    )

    # Surface form is only a hint. Domain, stakes, epistemic mode and exact
    # deliverable remain unresolved until a capable route interprets the query.
    contract = {
        "version": VERSION,
        "state": "multi_intent_candidate" if multi_intent else ("single_intent_candidate" if normalized else "unknown"),
        "task": {
            "primary": (f"{task_candidate.get('type')}_candidate" if task_candidate.get("type") != "unknown" and not multi_intent else "unresolved"),
            "secondary": [],
            "semantic_resolution": "required",
            "candidate_source": "conservative_surface_signal" if task_candidate.get("type") != "unknown" else "none",
            "surface_form": "question" if has_question else ("instruction_or_statement" if normalized else "empty"),
        },
        "domain": {"primary": "unknown", "subdomain": "unknown"},
        "stakes": {"level": "unknown", "consequence_of_error": "not_assessed"},
        "requested_outcome": ("recover_existing_personal_reference" if personal_reference else ("critically_examine_archive_worldview" if reflexive_critique_plan else ("distinguish_evidence_interpretation_hypothesis_and_normative_judgment" if epistemic_category_distinction else "unresolved"))),
        "institutional_critique": {"detected": bool(reflexive_critique_plan), "target": "living_archive_worldview" if reflexive_critique_plan else "unresolved", "mode": "reflexive_institutional_critique" if reflexive_critique_plan else "not_applicable", "evaluation_dimensions": reflexive_critique_plan["evaluation_dimensions"] if reflexive_critique_plan else [], "anti_defensiveness_required": bool(reflexive_critique_plan), "evidence_boundary": "distinguish_archive_claims_from_independent_validation" if reflexive_critique_plan else "not_applicable", "answer_requirements": reflexive_critique_plan["answer_requirements"] if reflexive_critique_plan else [], "response_contract": reflexive_critique_plan["response_contract"] if reflexive_critique_plan else {}},
        "personal_reference": {
            "detected": personal_reference,
            "version": PERSONAL_REFERENCE_VERSION,
            "resolution": "retrieve_and_verify_before_answering" if personal_reference else "not_applicable",
            "route_candidate": "teaching_conflict_discernment" if teaching_conflict_reference else ("general_personal_reference" if personal_reference else "not_applicable"),
            "evidence_scope": "available_conversation_and_retrieved_sources",
            "absence_claim_boundary": "not_found_in_available_context_only",
        },
        "audience": "unspecified",
        "constraints": {
            "no_handoff": no_handoff,
            "no_external_research": no_external_research,
            "no_followup": no_handoff,
        },
        "reasoning_mode": "critical_evaluation" if reflexive_critique_plan else ("epistemic_category_distinction" if epistemic_category_distinction else "unresolved"),
        "evidence": {
            "standard": "route_to_determine",
            "provenance_required": True,
        },
        "uncertainty": {
            "material_unknowns": ["task", "domain", "stakes", "requested_outcome"],
            "classification_confidence": "not_scored",
            "task_candidate_confidence": "not_semantically_certified",
        },
        "response": {
            "shape": "task_adaptive",
            "completion_criteria": ["answer_the_actual_request", "respect_explicit_constraints", "state_material_limits"],
        },
        "resolution": {
            "clarification": "only_if_materially_needed",
            "abstention": "if_reliable_completion_is_not_possible",
            "handoff": "prohibited" if no_handoff else "optional_if_relevant_and_verified",
            "followup": "prohibited" if no_handoff else "only_if_materially_useful",
        },
    }

    if meta_coverage_policy:
        contract["domain"] = {
            "primary": "guide_meta_governance_candidate",
            "subdomain": "archive_coverage_gap_policy",
        }
        contract["requested_outcome"] = "explain_evidence_threshold_for_archive_gap_claim"
        contract["reasoning_mode"] = "bounded_evidence_policy_adjudication"
        contract["evidence"] = {
            "standard": "four_outcome_coverage_policy_contract",
            "provenance_required": True,
        }
        contract["uncertainty"]["material_unknowns"] = [
            "specific_archive_subject_coverage_is_not_being_assessed"
        ]
        contract["response"] = {
            "shape": "bounded_four_outcome_policy_explanation",
            "completion_criteria": [
                "distinguish_direct_coverage",
                "distinguish_adjacent_coverage",
                "require_verified_evidence_for_genuine_gap",
                "separate_retrieval_or_verification_failure",
                "suppress_archive_resource_handoff",
            ],
        }
        contract["resolution"]["handoff"] = "not_applicable_for_policy_question"
        contract["meta_governance"] = meta_governance_contract
    elif epistemic_category_distinction:
        contract["domain"] = {
            "primary": "epistemology_and_reasoning",
            "subdomain": "evidence_interpretation_hypothesis_normative_judgment",
        }
        contract["requested_outcome"] = "distinguish_evidence_interpretation_hypothesis_and_normative_judgment"
        contract["reasoning_mode"] = "epistemic_category_distinction"
        contract["evidence"] = {
            "standard": "bounded_epistemic_category_framework",
            "provenance_required": False,
        }
        contract["uncertainty"]["material_unknowns"] = [
            "whether_the_visitor_wants_a_field_specific_formal_definition"
        ]
        contract["response"] = {
            "shape": "four_category_distinction_with_relationships",
            "completion_criteria": [
                "define_all_four_categories",
                "distinguish_evidence_from_interpretation",
                "distinguish_hypothesis_from_established_fact",
                "make_values_and_normative_premises_explicit",
                "explain_how_the_categories_constrain_one_another",
                "include_a_concrete_example",
            ],
        }
        contract["epistemic_distinction"] = epistemic_distinction_contract

    return contract


def validate_question_contract(contract: Any) -> Dict[str, Any]:
    """Validate contract shape; this is schema integrity, not semantic adequacy."""
    if not isinstance(contract, dict):
        return {"valid": False, "reason": "not_object"}
    required = ("version", "state", "task", "domain", "stakes", "requested_outcome", "personal_reference",
                "constraints", "reasoning_mode", "evidence", "uncertainty", "response", "resolution")
    missing = [key for key in required if key not in contract]
    if missing:
        return {"valid": False, "reason": "missing_fields", "missing": missing}
    if contract.get("version") != VERSION:
        return {"valid": False, "reason": "unsupported_version"}
    if contract.get("state") not in {"unknown", "single_intent_candidate", "multi_intent_candidate"}:
        return {"valid": False, "reason": "invalid_state"}
    if not isinstance(contract.get("personal_reference"), dict) or not isinstance(contract.get("constraints"), dict) or not isinstance(contract.get("resolution"), dict):
        return {"valid": False, "reason": "invalid_nested_shape"}
    return {"valid": True, "reason": "schema_valid_not_semantically_certified"}
