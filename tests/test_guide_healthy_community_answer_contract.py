"""Regression tests for answer-first healthy-community newcomer questions."""
import main


QUERY = (
    "I'm new to the Living Archive. I care about healthier communities, "
    "but I don't know its vocabulary or where to begin."
)


def test_healthy_community_newcomer_query_is_detected():
    assert main._is_healthy_community_orientation_question(QUERY)


def test_healthy_community_answer_is_substantive_and_accessible():
    answer = main._healthy_community_answer_recovery().casefold()
    assert "participate" in answer
    assert "raise concerns" in answer
    assert "whose voices are heard" in answer
    assert "excluded or harmed" in answer
    assert "you do not need to know the living archive's vocabulary" in answer
    assert "what detail or context would make this question most concrete" not in answer


def test_pure_navigation_without_healthy_community_topic_is_not_captured():
    assert not main._is_healthy_community_orientation_question(
        "I'm new to the Living Archive. Where should I begin?"
    )


def test_healthy_community_topic_without_newcomer_language_is_not_overcaptured():
    assert not main._is_healthy_community_orientation_question(
        "What makes a healthy community resilient over time?"
    )


def test_unrelated_personal_topic_is_not_captured():
    assert not main._is_healthy_community_orientation_question(
        "I'm new to the Living Archive and want to understand trust in close relationships."
    )
