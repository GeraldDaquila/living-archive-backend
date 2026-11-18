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


def test_healthy_community_canonical_doorway_has_renderer_required_rationale():
    doorway = main._healthy_community_canonical_recommendation(QUERY, {})
    assert doorway is not None
    assert doorway["title"] == "What Healthy Communities Actually Look Like"
    assert doorway["url"] == (
        "https://geralddaquila.com/2025/10/07/"
        "t4-codex-overflow-communities-governance-by-resonance/"
    )
    assert doorway["rationale"]
    assert "healthier communities" in doorway["rationale"].casefold()


def test_terminal_doorway_boundary_preserves_healthy_community_recommendation():
    doorway = main._healthy_community_canonical_recommendation(QUERY, {})
    result = main._guide_restore_verified_doorway(
        {"response": main._healthy_community_answer_recovery(),
         "recommendation": doorway},
        QUERY,
    )
    assert result["recommendation"] == doorway
    assert result["canonical_doorway"] == doorway
    assert result["doorway_title"] == doorway["title"]
    assert result["doorway_url"] == doorway["url"]
    assert result["doorway_rationale"] == doorway["rationale"]
