"""Gold Star regression contract for personal regeneration-invitation discernment."""

import main
from deterministic_answer_recovery import (
    compose_recovery,
    is_regeneration_participation_question,
    registered_recovery_recommendation,
)


QUERY = (
    "Where am I being invited to participate in regeneration rather than merely "
    "consume spiritual content about it?"
)


def test_exact_question_is_classified_as_regenerative_participation():
    assert is_regeneration_participation_question(QUERY)


def test_answer_distinguishes_existing_responsibility_emerging_opportunity_and_premature_invitation():
    answer = compose_recovery(QUERY)
    paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]

    assert len(paragraphs) == 5
    assert paragraphs[1].startswith("1. EXISTING RESPONSIBILITY")
    assert paragraphs[2].startswith("2. EMERGING OPPORTUNITY")
    assert paragraphs[3].startswith("3. PREMATURE OR UNSUPPORTED INVITATION")
    assert paragraphs[4].startswith("A practical first move:")
    for required in (
        "existing responsibility",
        "emerging opportunity",
        "premature or unsupported invitation",
        "real relationship, role, commitment, or shared undertaking",
        "the people affected should help define the problem",
        "the affected people's consent",
        "not three spiritual labels to assign yourself",
    ):
        assert required.casefold() in answer.casefold()


def test_answer_prioritizes_existing_responsibility_and_requires_listening_before_offering():
    answer = compose_recovery(QUERY)
    assert "1. EXISTING RESPONSIBILITY" in answer
    assert answer.index("1. EXISTING RESPONSIBILITY") < answer.index("2. EMERGING OPPORTUNITY") < answer.index("3. PREMATURE OR UNSUPPORTED INVITATION")
    assert "A practical first move:" in answer
    assert "explore an emerging opportunity by listening before offering a solution" in answer
    assert "proportionate, reversible step" in answer
    assert "remain answerable to the people affected" in answer


def test_answer_preserves_spiritual_epistemic_boundary_and_user_agency():
    answer = compose_recovery(QUERY)
    assert "You do not need to treat every spiritual impression as a command" in answer
    assert "not the amount of content consumed or the intensity of the feeling" in answer
    assert "supernatural invitation has occurred" in answer


def test_existing_canonical_doorway_is_preserved_and_question_specific():
    doorway = registered_recovery_recommendation(QUERY)
    assert doorway["title"] == "Stewardship as Human Maturity"
    assert doorway["url"] == (
        "https://geralddaquila.com/2026/07/06/stewardship-as-human-maturity/"
    )
    assert "not a claim about a supernatural calling" in doorway["rationale"]


def test_final_visitor_boundary_restores_refined_answer_and_verified_doorway():
    result = main._guide_finalize_visitor_payload(
        {
            "response": "The invitation is to follow what feels meaningful.",
            "recommendation": {
                "title": "Unrelated resource",
                "url": "https://example.com/unrelated",
            },
        },
        QUERY,
    )
    assert result["response"] == compose_recovery(QUERY)
    assert "existing responsibility" in result["response"]
    assert "emerging opportunity" in result["response"]
    assert "premature or unsupported invitation" in result["response"]
    assert result["recommendation"]["title"] == "Stewardship as Human Maturity"
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_title"] == "Stewardship as Human Maturity"


def test_classifier_does_not_capture_general_regeneration_or_spiritual_content_questions():
    for question in (
        "What is regeneration?",
        "Why is spiritual content meaningful?",
        "How can a community regenerate its local ecosystem?",
        "What does stewardship mean?",
    ):
        assert not is_regeneration_participation_question(question), question
