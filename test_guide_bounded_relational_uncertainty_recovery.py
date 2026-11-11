"""Regression tests for humane deterministic recovery under relational uncertainty."""

import main


def test_friendship_care_uncertainty_gets_humane_bounded_response():
    result = main._basic_inquiry_round1_deterministic_response(
        "I feel foolish for still caring about this friendship.",
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )

    response = result["response"]
    assert result["provider"] == "bounded_relational_uncertainty_recovery"
    assert "isn't foolish to care" in response
    assert "two different things" in response
    assert "what makes you feel foolish" in response
    assert result["doorway_title"] == ""
    assert "they are toxic" not in response.lower()
    assert "you should leave" not in response.lower()


def test_relational_uncertainty_does_not_claim_to_know_other_persons_motives():
    result = main._basic_inquiry_round1_deterministic_response(
        "I feel stupid for still loving someone after our relationship changed.",
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )

    response = result["response"].lower()
    assert result["provider"] == "bounded_relational_uncertainty_recovery"
    assert "their motives" not in response
    assert "they never cared" not in response
    assert "you must move on" not in response


def test_unrelated_foolishness_does_not_trigger_relational_recovery():
    result = main._basic_inquiry_round1_deterministic_response(
        "I feel foolish for making a mistake in my presentation.",
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )

    assert result.get("provider") != "bounded_relational_uncertainty_recovery"


def test_conceptual_recovery_preserves_verified_authoritative_doorway():
    doorway = {
        "title": "Relevant Archive Resource",
        "url": "https://geralddaquila.com/relevant-resource/",
    }
    result = main._basic_inquiry_round1_deterministic_response(
        "What is the difference between genuine transformation and temporary emotional relief?",
        {},
        {
            "context_blocks": "",
            "authoritative_doorway": doorway,
        },
        recommendation_available=True,
    )

    assert result["provider"] == "bounded_conceptual_relationship_recovery"
    assert result["recommendation"] == doorway
    assert result["doorway_title"] == doorway["title"]
    assert result["doorway_url"] == doorway["url"]
