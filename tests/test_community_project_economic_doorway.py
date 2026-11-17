"""Regression tests for community-project economic accounting and canonical navigation."""

import general_guide_composition as composition
import main


QUERY = (
    "A community project reports financial return and volunteer hours but not who "
    "benefits or what common resources are maintained. What additional economic "
    "dimensions should the Guide surface?"
)


def test_screenshot_question_enters_community_project_economic_contract():
    assert composition._requires_community_project_economic_dimensions(QUERY)
    assert main._select_verified_doorway_conceptual_family(QUERY) == (
        "community_project_economic_dimensions"
    )


def test_recovery_surfaces_distribution_sustaining_costs_and_long_horizon():
    answer = composition._community_project_economic_dimensions_recovery()
    assert composition._has_community_project_economic_dimensions_explanation(answer)
    assert len(answer.split("\n\n")) == 3
    assert "who receives the project's benefits" in answer
    assert "replacement of shared assets" in answer
    assert "not conclusions about this particular project" in answer


def test_final_visitor_boundary_repairs_abstention_and_emits_canonical_doorway():
    result = main._guide_finalize_visitor_payload(
        {
            "response": (
                "I do not have enough grounded material here to give a specific "
                "Archive-based answer."
            ),
            "recommendation": None,
            "canonical_doorway": None,
        },
        QUERY,
    )
    assert result["processing"] == (
        "final_visitor_boundary_community_project_economic_dimensions"
    )
    assert composition._has_community_project_economic_dimensions_explanation(
        result["response"]
    )
    expected = {
        "title": "Local Resilience Economies",
        "url": "https://geralddaquila.com/2026/05/27/local-resilience-economies/",
    }
    assert result["recommendation"]["title"] == expected["title"]
    assert result["recommendation"]["url"] == expected["url"]
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_title"] == expected["title"]
    assert result["doorway_url"] == expected["url"]
    assert "particular project" in result["response"]


def test_adequate_provider_answer_is_preserved_but_doorway_is_still_enforced():
    answer = (
        "The project should report who receives its benefits and how they are "
        "distributed across the community.\n\n"
        "It should also count volunteer labor and the costs of maintaining shared "
        "resources and assets, including who carries that responsibility.\n\n"
        "A long-term account should track lifecycle effects, local value retained, "
        "and who is accountable for review and correction over time."
    )
    result = main._guide_finalize_visitor_payload(
        {"response": answer, "recommendation": None},
        QUERY,
    )
    assert result["response"] == answer
    assert result["doorway_title"] == "Local Resilience Economies"
    assert result["recommendation"]["url"] == (
        "https://geralddaquila.com/2026/05/27/local-resilience-economies/"
    )
