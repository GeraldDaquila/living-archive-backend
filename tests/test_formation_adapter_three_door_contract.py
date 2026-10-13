"""Formation adapter must satisfy the visitor-facing three-door contract."""

from formation_adapter import FormationAdapter
from specialist_adapters import SpecialistAdapterContext


def run_formation(situation: str, possibility: str):
    return FormationAdapter().process(
        SpecialistAdapterContext(
            request_id="formation-e2e-test",
            guide_version="test",
            specialist_id="formation",
            original_question=situation,
            recognized_territory="stewardship formation",
            processing_purpose="bounded formation navigation",
            guide_context={
                "choice": "carrying",
                "situation": situation,
                "possibility": possibility,
            },
            safety_state="green",
        )
    )


def test_responsibility_that_depends_on_one_person_returns_three_distinct_doors():
    result = run_formation(
        "I have taken on a larger responsibility and want to understand how to carry it without making everything depend on me.",
        "I hope to become more steady and able to carry responsibility differently.",
    )
    doors = result["canonical_candidates"]
    assert len(doors) == 3
    assert len({door["id"] for door in doors}) == 3
    assert {door["id"] for door in doors} == {
        "learning_arcs",
        "governance_foundations",
        "stewardship_frameworks",
    }
    assert all(door["title"] and door["url"].startswith("https://geralddaquila.com/") for door in doors)


def test_practice_only_request_still_returns_three_distinct_canonical_doors():
    result = run_formation(
        "I want to become more capable in an area that matters.",
        "I hope to apply what I learn in practice.",
    )
    doors = result["canonical_candidates"]
    assert len(doors) == 3
    assert len({door["id"] for door in doors}) == 3
