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


def test_live_basic_inquiry_routes_meta_coverage_policy_before_retrieval_or_provider(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Meta-coverage policy route must not invoke retrieval or a provider.")

    monkeypatch.setattr(main.use_core, "fetch_canonical_context", forbidden)
    monkeypatch.setattr(main, "route_with_model_bank", forbidden)

    payload = main._basic_inquiry_response(QUESTION)
    assert recovery.has_guide_meta_coverage_policy_explanation(payload["response"])
    assert payload["processing"] == "guide_meta_coverage_policy_deterministic"
    assert payload["route_source"] == "guide_meta_coverage_policy_early_boundary"
    assert payload["response_provenance"]["llm_invoked"] is False
    assert payload["recommendation"] is None
    assert payload["canonical_doorway"] is None
    assert payload["doorway_decision"] == "omit"


def test_outer_terminal_boundary_repairs_policy_answer_and_suppresses_every_doorway_alias():
    payload = {
        "response": "I did not find a directly relevant resource.",
        "recommendation": {"title": "Unrelated", "url": "https://geralddaquila.com/unrelated/"},
        "canonical_doorway": {"title": "Unrelated", "url": "https://geralddaquila.com/unrelated/"},
        "doorway_title": "Unrelated",
        "doorway_url": "https://geralddaquila.com/unrelated/",
        "authoritative_doorway": {"title": "Unrelated", "url": "https://geralddaquila.com/unrelated/"},
        "canonical_recommendation": {"title": "Unrelated", "url": "https://geralddaquila.com/unrelated/"},
        "archive_doorway": {"title": "Unrelated", "url": "https://geralddaquila.com/unrelated/"},
        "recommendation_canonical_primary": {"title": "Unrelated", "url": "https://geralddaquila.com/unrelated/"},
    }

    result = main._guide_enforce_terminal_doorway_policy(payload, QUESTION)

    assert recovery.has_guide_meta_coverage_policy_explanation(result["response"])
    for key in (
        "recommendation", "canonical_doorway", "doorway_title", "doorway_url",
        "authoritative_doorway", "canonical_recommendation", "archive_doorway",
        "recommendation_canonical_primary",
    ):
        assert result[key] is None
    assert result["doorway_decision"] == "omit"
    assert result["navigation_suppressed_by_task_contract"] is True
    assert "coverage policy" in result["doorway_omission_reason"]


def test_meta_policy_recovery_is_not_rejected_by_generic_nonanswer_heuristics(monkeypatch):
    answer = recovery.compose_recovery(QUESTION)
    monkeypatch.setattr(composition, "is_generic_nonanswer", lambda *args, **kwargs: True)
    monkeypatch.setattr(composition, "is_meta_answer_failure", lambda *args, **kwargs: True)

    assert main._guide_outer_registered_recovery_is_valid(QUESTION, answer) is True


def test_meta_coverage_policy_answer_passes_the_shared_response_floor():
    from gold_star_response_floor import apply_response_floor_boundary

    payload = main._basic_inquiry_response(QUESTION)
    safe, status = apply_response_floor_boundary(QUESTION, payload, 200)

    assert status == 200
    assert recovery.has_guide_meta_coverage_policy_explanation(safe["response"])
    assert safe["gold_star_v2_quality_floor"]["status"] != "fail"


def test_answer_envelope_marks_meta_policy_doorway_as_prohibited_by_task_contract():
    from gold_star_answer_envelope import build_answer_envelope
    from gold_star_question_contract import build_question_contract

    payload = main._basic_inquiry_response(QUESTION)
    envelope = build_answer_envelope(
        QUESTION,
        payload,
        build_question_contract(QUESTION),
    )

    assert envelope["doorway"]["state"] == "intentionally_omitted_with_reason"
    assert envelope["doorway"]["prohibited_by_question_contract"] is True
