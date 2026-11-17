"""Regression tests for spiritual-community authority and accountability answers."""
import re

import main
from deterministic_answer_recovery import (
    compose_recovery,
    has_registered_recovery,
    is_spiritual_community_accountability_question,
    registered_recovery_recommendation,
)
from general_guide_composition import enforce_response_contracts


QUERY = (
    "A spiritual community has charismatic leadership and weak accountability. "
    "How should the Guide identify the risks without dismissing spiritual practice itself?"
)

EXPECTED_DOORWAY = {
    "title": "Community Accountability Systems",
    "url": "https://geralddaquila.com/2026/05/16/community-accountability-systems/",
    "rationale": (
        "This Archive essay examines how communities prevent power from becoming insulated from feedback through "
        "transparent, distributed accountability, clear boundaries, protected dissent, and repair. It directly "
        "addresses the risks of charismatic leadership and weak accountability without treating spiritual belief "
        "or practice itself as the problem."
    ),
}


def test_spiritual_community_accountability_question_is_narrowly_classified():
    assert is_spiritual_community_accountability_question(QUERY)
    assert has_registered_recovery(QUERY)
    assert is_spiritual_community_accountability_question(
        "A faith community has a charismatic leader and limited oversight. How can risks be assessed while respecting its spiritual practice?"
    )


def test_spiritual_community_accountability_classifier_does_not_capture_adjacent_questions():
    for question in (
        "How can a spiritual community deepen its shared practice?",
        "What makes charismatic leadership effective in a company?",
        "How can a secular neighborhood group improve accountability?",
        "What are the risks of weak accountability in a software team?",
        "How should a spiritual community welcome newcomers?",
    ):
        assert not is_spiritual_community_accountability_question(question)


def test_spiritual_community_recovery_is_three_paragraphs_and_preserves_the_governing_distinction():
    answer = compose_recovery(QUERY)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", answer) if part.strip()]

    assert len(paragraphs) == 3
    assert "Spiritual practice and the way a community governs its authority are different things." in paragraphs[0]
    assert "not a verdict on the community's beliefs" in paragraphs[0]
    assert "observable patterns" in paragraphs[1]
    assert "A single disagreement is not proof of abuse" in paragraphs[1]
    assert "genuinely independent council" in paragraphs[2]
    assert "question, decline, and leave without retaliation" in paragraphs[2]
    assert "A spiritual community has charismatic leadership" not in answer
    assert QUERY not in answer
    assert not re.search(r"\b(?:AI|artificial intelligence|provider|retrieval)\b", answer, re.I)


def test_spiritual_community_recovery_owns_its_canonical_doorway():
    assert registered_recovery_recommendation(QUERY) == EXPECTED_DOORWAY
    assert main._select_verified_doorway_conceptual_family(QUERY) == "spiritual_community_accountability"
    assert main._select_guide_node_fallback_doorway(QUERY) == EXPECTED_DOORWAY


def test_provider_composition_contract_replaces_question_echo_and_off_frame_prose():
    contaminated = (
        "The risk of a spiritual community has charismatic leadership and weak accountability. "
        "A spiritual community has charismatic leadership and weak accountability. "
        "How should the Guide identify the risks without dismissing spiritual practice itself? "
        "It should ensure the risk of a spiritual community has charismatic leadership and weak accountability.\\n\\n"
        "The question asks about a spiritual community with charismatic leadership and weak accountability.\\n\\n"
        "AI can help identify the risks."
    )
    expected = compose_recovery(QUERY)

    assert enforce_response_contracts(QUERY, contaminated) == expected
    assert enforce_response_contracts(QUERY, expected) == expected
    assert QUERY not in expected


def test_provider_finalizer_restores_the_same_verified_doorway_without_rewriting_answer():
    answer = compose_recovery(QUERY)
    finalized = main._guide_finalize_visitor_payload(
        {"response": answer, "recommendation": None, "canonical_doorway": None},
        QUERY,
    )

    assert finalized["response"] == answer
    assert finalized["recommendation"] == EXPECTED_DOORWAY
    assert finalized["canonical_doorway"] == EXPECTED_DOORWAY
    assert finalized["doorway_title"] == EXPECTED_DOORWAY["title"]
    assert finalized["doorway_url"] == EXPECTED_DOORWAY["url"]
    assert finalized["doorway_rationale"] == EXPECTED_DOORWAY["rationale"]


def test_deterministic_route_binds_answer_and_doorway_together():
    answer = compose_recovery(QUERY)
    deterministic = main._basic_inquiry_round1_deterministic_response(
        QUERY, {}, {"context_blocks": ""}, recommendation_available=False
    )

    assert deterministic["response"] == answer
    assert deterministic["recommendation"] == EXPECTED_DOORWAY
    assert deterministic["doorway_title"] == EXPECTED_DOORWAY["title"]
    assert deterministic["doorway_url"] == EXPECTED_DOORWAY["url"]
