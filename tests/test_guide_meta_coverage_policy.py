"""Regression contract for The Guide's Archive coverage-gap declaration policy."""

import deterministic_answer_recovery as recovery
import general_guide_composition as composition
import main


QUESTION = 'When should The Guide say “the Archive does not yet address this directly”?'


def test_query_level_recognizes_meta_coverage_policy_question_and_paraphrases():
    assert recovery.is_guide_meta_coverage_policy_question(QUESTION)
    assert recovery.is_guide_meta_coverage_policy_question(
        "Under what conditions should the Guide acknowledge that the Archive has no direct coverage?"
    )
    assert recovery.is_guide_meta_coverage_policy_question(
        "What evidence should the Guide have before saying the Archive does not cover a subject?"
    )


def test_meta_coverage_question_is_not_routed_as_resource_recommendation():
    profile = main._base._inquiry_profile(QUESTION)
    assert profile.get("action") in {"foundation", "conceptual"}
    assert not profile.get("recommendation")
    assert not profile.get("navigation")
    assert main._guide_subject_discovery_query(QUESTION) == ""
    assert main._general_guide_authoritative_doorway(QUESTION, {}) is None


def test_meta_coverage_policy_recovery_distinguishes_search_failure_from_archive_gap():
    answer = recovery.compose_recovery(QUESTION)
    assert "missing retrieval result" in answer
    assert "related" in answer
    assert "indexing" in answer
    assert "couldn't verify a resource" in answer
    assert "whole Archive" in answer


def test_final_composition_boundary_replaces_resource_abstention_with_policy_answer():
    abstention = (
        "Your question asks when the Guide should say the Archive does not yet address this directly. "
        "I did not identify a directly relevant Archive resource to recommend for this question."
    )
    answer = composition.enforce_response_contracts(QUESTION, abstention)
    assert "missing retrieval result" in answer
    assert "whole Archive" in answer
    assert "did not identify a directly relevant Archive resource" not in answer


def test_unrelated_resource_discovery_and_ordinary_coverage_questions_are_not_captured():
    negatives = (
        "Where can I find resources about institutional responsibility?",
        "Does the Archive address institutional responsibility directly?",
        "What should I read about governance?",
        "When should the Archive address climate adaptation?",
    )
    assert all(not recovery.is_guide_meta_coverage_policy_question(q) for q in negatives)


def test_valid_provider_policy_answer_is_preserved():
    answer = (
        "The Guide should only make that claim after it has checked the relevant canonical "
        "sources and verified that none directly addresses the question. A related resource "
        "must be described as related, not direct. A failed retrieval or indexing problem "
        "does not establish an Archive coverage gap."
    )
    assert recovery.has_guide_meta_coverage_policy_explanation(answer)
    assert composition.enforce_response_contracts(QUESTION, answer) == answer
