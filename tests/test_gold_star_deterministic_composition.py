"""Contracts for provider-independent, governed Gold Star structural application."""
import json
from pathlib import Path

import main
import gold_star_lessons
from gold_star_deterministic_composition import compose_deterministic_gold_star_response


ETHICAL = {
    "benchmark_id": "general-guide-ethical-tradeoff-2026-10",
    "reasoning_family": "ethical_tradeoff_and_conflicting_harms",
    "discipline": "Make competing claims visible, examine power and irreversible harms, use defensible criteria, acknowledge sacrifice, and test whether burdens fall unfairly on those with least power.",
    "abstention_boundary": "Do not force false consensus, conceal sacrifice, shift burdens unfairly onto people with least power, or invent an unverified doorway URL.",
    "authority_mode": "deterministic_structural_guidance_only",
}


def test_deterministic_plan_applies_discipline_and_abstention_boundary_without_copying_lesson():
    result = compose_deterministic_gold_star_response(
        "A neighborhood group must choose between two options that protect different interests. How should it decide?",
        ETHICAL,
    )
    assert result is not None
    assert result["plan_id"] == "ethical_tradeoff_v1"
    assert result["abstention_boundary_applied"] is True
    assert len(result["application_evidence_spans"]) == 2
    assert "false consensus" in result["response"]
    assert "least power" in result["response"]
    assert ETHICAL["discipline"] not in result["response"]
    assert ETHICAL["abstention_boundary"] not in result["response"]


def test_unknown_or_incompatible_lesson_fails_closed():
    unrelated = dict(ETHICAL, reasoning_family="unregistered_family")
    assert compose_deterministic_gold_star_response("How should we decide?", unrelated) is None
    incompatible = dict(ETHICAL, abstention_boundary="Do not overgeneralize.")
    assert compose_deterministic_gold_star_response("How should we decide?", incompatible) is None


def test_main_deterministic_fallback_consumes_eligible_gold_star(monkeypatch):
    monkeypatch.setattr(
        gold_star_lessons,
        "deterministic_fallback_contribution",
        lambda _query: dict(ETHICAL),
    )
    query = "How should a neighborhood group choose between two plans when each protects an important interest but creates a different loss?"
    result = main._basic_inquiry_round1_deterministic_response(query, {}, {})
    assert result["provider"] == "gold_star_deterministic_structural_fallback"
    assert "competing interests and possible losses" in result["response"]
    assert "false consensus" in result["response"]
    assert "least power" in result["response"]


def test_provider_exhaustion_deterministic_application_updates_request_adjudication_trace():
    query = (
        "How should a group decide what to protect when one person's priorities mean "
        "another person will lose something deeply valued?"
    )
    import gold_star_adjudication_trace as trace

    token = trace.begin_request_context("abcdef0123456789abcdef0123456789")
    try:
        trace.begin_composition_attempt()
        contribution = gold_star_lessons.active_quality_contribution(query)
        assert contribution is not None
        initial = trace.build_adjudication_trace(contribution)
        assert initial["selection"] == "not_observed"
        assert initial["application"] == "not_observed"

        result = main._basic_inquiry_provider_exhaustion_response(query, {}, {})
        assert result["provider"] == "gold_star_deterministic_structural_fallback"

        applied = trace.current_attempt_trace()
        assert applied["request_id"] == "abcdef0123456789abcdef0123456789"
        assert applied["provider_adjudication_status"] == "not_observed"
        assert applied["selection"] == "deterministic_renderer_selected"
        assert applied["selected_candidate_ids"] == [result.get("benchmark_id", applied["selected_candidate_ids"][0])]
        assert applied["application"] == "deterministic_renderer_applied"
        assert applied["application_evidence_present"] is True
        assert applied["application_evidence_candidate_ids"] == applied["selected_candidate_ids"]
        assert applied["deterministic_application_span_count"] == 2
        assert trace.validate_trace(applied)["valid"]

        final = trace.mark_final_delivery(
            applied,
            provider_candidate_delivered=False,
            final_provenance="deterministic_recovery",
        )
        assert final["final_delivery"] == "deterministic_or_unresolved_replacement"
        assert final["application"] == "deterministic_renderer_applied"
        assert trace.validate_trace(final)["valid"]
    finally:
        trace.end_request_context(token)


def test_community_rule_gold_stars_remain_excluded_from_deterministic_fallback():
    query = "How should a community balance personal liberty with collective obligations when setting a fair rule?"
    assert gold_star_lessons.deterministic_fallback_contribution(query) is None


def test_provider_exhaustion_community_tradeoff_path_survives_early_branch_finalization():
    query = (
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both fair and workable?"
    )
    # These newer community-rule lessons are provider-only by registry policy.
    assert gold_star_lessons.deterministic_fallback_contribution(query) is None
    result = main._basic_inquiry_provider_exhaustion_response(query, {}, {})
    assert result["response"].strip()
    assert result["provider"] != "gold_star_deterministic_structural_fallback"
    import general_guide_composition
    assert not general_guide_composition.is_generic_nonanswer(query, result["response"])
    assert not general_guide_composition.is_meta_answer_failure(result["response"])


def test_unseen_tradeoff_question_retrieves_and_applies_registered_deterministic_gold_star():
    query = (
        "How should a group decide what to protect when one person's priorities mean "
        "another person will lose something deeply valued?"
    )
    contribution = gold_star_lessons.deterministic_fallback_contribution(query)
    assert contribution is not None
    assert contribution["benchmark_id"] == "general-guide-ethical-tradeoff-2026-10"
    assert contribution["reasoning_family"] == "ethical_tradeoff_and_conflicting_harms"
    assert contribution["authority_mode"] == "deterministic_structural_guidance_only"

    result = compose_deterministic_gold_star_response(query, contribution)
    assert result is not None
    assert result["plan_id"] == "ethical_tradeoff_v1"
    assert result["abstention_boundary_applied"] is True
    assert len(result["application_evidence_spans"]) == 2
    assert "false consensus" in result["response"]
    assert "least power" in result["response"]


def test_deterministic_eligible_registry_and_transfer_review_families_are_consistent():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    review_by_id = {entry["benchmark_id"]: entry for entry in review["entries"]}

    mismatches = []
    for record in registry["records"]:
        capabilities = record.get("gold_star_capabilities") or {}
        if not capabilities.get("deterministic_fallback_eligible"):
            continue
        entry = review_by_id.get(record["benchmark_id"])
        if entry is None:
            continue
        registry_family = str(capabilities.get("reasoning_family") or "").strip()
        review_family = str(entry.get("reasoning_family") or "").strip()
        if registry_family and review_family and registry_family != review_family:
            mismatches.append((record["benchmark_id"], registry_family, review_family))

    assert mismatches == []

def test_unseen_tradeoff_question_reaches_real_deterministic_response_boundary_without_mocks():
    query = (
        "How should a group decide what to protect when one person's priorities mean "
        "another person will lose something deeply valued?"
    )

    # This is the same production selector used by the deterministic fallback;
    # no injected contribution or mocked selector is permitted in this test.
    contribution = gold_star_lessons.deterministic_fallback_contribution(query)
    assert contribution is not None
    assert contribution["benchmark_id"] == "general-guide-ethical-tradeoff-2026-10"
    assert contribution["authority_mode"] == "deterministic_structural_guidance_only"

    result = main._basic_inquiry_round1_deterministic_response(query, {}, {})

    assert result["provider"] == "gold_star_deterministic_structural_fallback"
    assert "competing interests and possible losses" in result["response"]
    assert "false consensus" in result["response"]
    assert "least power" in result["response"]
    assert result["model"] == ""


def test_provider_exhaustion_boundary_applies_registered_deterministic_gold_star_before_conceptual_fallback():
    query = (
        "How should a group decide what to protect when one person's priorities mean "
        "another person will lose something deeply valued?"
    )
    # Exercise the real provider-exhaustion recovery boundary with the live
    # registry selector and deterministic renderer; no retrieval or renderer mocks.
    result = main._basic_inquiry_provider_exhaustion_response(query, {}, {})
    assert result["provider"] == "gold_star_deterministic_structural_fallback"
    assert "competing interests and possible losses" in result["response"]
    assert "false consensus" in result["response"]
    assert "least power" in result["response"]


def test_unrelated_physical_science_question_does_not_receive_ethical_tradeoff_plan():
    query = "Why does a metal spoon feel colder than a wooden spoon in the same room?"

    contribution = gold_star_lessons.deterministic_fallback_contribution(query)
    assert contribution is None or contribution.get("reasoning_family") != (
        "ethical_tradeoff_and_conflicting_harms"
    )

    result = main._basic_inquiry_round1_deterministic_response(query, {}, {})

    assert result["provider"] != "gold_star_deterministic_structural_fallback"
    assert "competing interests and possible losses" not in result["response"]
