"""Contracts for provider-independent, governed Gold Star structural application."""
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
