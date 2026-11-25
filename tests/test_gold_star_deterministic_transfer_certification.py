"""Provider-independent held-out tests for deterministic Gold Star transfer.

These tests measure only reviewed renderer families. Registry eligibility alone
is not treated as proof that a family has a deterministic response plan.
"""
import pytest

import main
import gold_star_lessons
from gold_star_deterministic_composition import (
    _PLANS,
    compose_deterministic_gold_star_response,
)


HELD_OUT_CASES = (
    {
        "case_id": "ethical-tradeoff-unseen-01",
        "query": (
            "How should a group decide what to protect when one person's priorities "
            "mean another person will lose something deeply valued?"
        ),
        "family": "ethical_tradeoff_and_conflicting_harms",
        "plan_id": "ethical_tradeoff_v1",
        "evidence_terms": ("competing interests and possible losses", "false consensus", "least power"),
    },
    {
        "case_id": "stakeholder-obligations-unseen-01",
        "query": (
            "How should leaders balance competing stakeholder obligations when employees, customers, "
            "and local residents have conflicting interests?"
        ),
        "family": "stakeholder_tradeoffs",
        "plan_id": "stakeholder_tradeoffs_v1",
        "evidence_terms": ("legitimate rights", "who benefits", "review and correct the decision"),
    },
)


@pytest.mark.parametrize("case", HELD_OUT_CASES, ids=lambda case: case["case_id"])
def test_unseen_supported_family_retrieves_and_renders_deterministically(case):
    contribution = gold_star_lessons.deterministic_fallback_contribution(case["query"])

    assert contribution is not None
    assert contribution["reasoning_family"] == case["family"]
    assert contribution["authority_mode"] == "deterministic_structural_guidance_only"
    assert case["family"] in _PLANS

    rendered = compose_deterministic_gold_star_response(case["query"], contribution)
    assert rendered is not None
    assert rendered["plan_id"] == case["plan_id"]
    assert rendered["abstention_boundary_applied"] is True
    assert len(rendered["application_evidence_spans"]) == 2
    for term in case["evidence_terms"]:
        assert term in rendered["response"]
    assert contribution["discipline"] not in rendered["response"]
    assert contribution["abstention_boundary"] not in rendered["response"]


@pytest.mark.parametrize("case", HELD_OUT_CASES, ids=lambda case: case["case_id"])
def test_real_provider_exhaustion_boundary_uses_supported_deterministic_plan(case):
    # No provider, retrieval, or renderer mocks: exercise the real recovery boundary.
    result = main._basic_inquiry_provider_exhaustion_response(case["query"], {}, {})

    assert result["provider"] == "gold_star_deterministic_structural_fallback"
    assert result["model"] == ""
    for term in case["evidence_terms"]:
        assert term in result["response"]


def test_ambiguous_stakeholder_distribution_question_does_not_receive_project_accounting_lesson():
    query = (
        "How can leaders weigh obligations to employees, customers, and local residents "
        "when a decision benefits one group but imposes costs on another?"
    )

    contribution = gold_star_lessons.deterministic_fallback_contribution(query)
    assert contribution is None


def test_unrelated_physical_science_question_does_not_receive_either_plan():
    query = (
        "Why does a metal spoon feel colder than a wooden spoon "
        "when both are at the same room temperature?"
    )

    contribution = gold_star_lessons.deterministic_fallback_contribution(query)
    assert contribution is None

    result = main._basic_inquiry_round1_deterministic_response(query, {}, {})
    assert result["provider"] != "gold_star_deterministic_structural_fallback"
    assert "competing interests and possible losses" not in result["response"]
    assert "legitimate rights" not in result["response"]


def test_ambiguous_stakeholder_recovery_does_not_reuse_exact_gold_standard_answer():
    from general_guide_gold_standards import (
        find_cross_question_standard_response,
        resolve_exact_gold_standard,
    )

    query = (
        "How can leaders weigh obligations to employees, customers, and local residents "
        "when a decision benefits one group but imposes costs on another?"
    )
    exact = resolve_exact_gold_standard("How can leaders hold competing stakeholder obligations?")
    assert exact is not None

    # The ambiguous negative control is not eligible for the community-project
    # deterministic lesson, but it remains answerable from bounded general knowledge.
    assert gold_star_lessons.deterministic_fallback_contribution(query) is None
    result = main._basic_inquiry_provider_exhaustion_response(query, {}, {})

    response = str(result.get("response") or "").strip()
    assert len(response) >= 400
    assert len(response.split("\n\n")) == 3
    assert response != exact["expected_response"]
    assert find_cross_question_standard_response(query, response) is None
    assert "community project accounting" not in response.casefold()
