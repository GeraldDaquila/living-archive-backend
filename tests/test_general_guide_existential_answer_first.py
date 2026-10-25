"""Regression tests for answer-first handling of broad existential questions."""

import general_guide_composition as guide
import main


def test_broad_existential_question_receives_substantive_answer_before_clarification():
    result = guide.compose(
        use_core=None,
        query="What is the meaning of life?",
        context_data={},
    )

    assert result is not None
    assert result["provider"] == "bounded_existential_general_knowledge_recovery"
    response = result["response"]
    paragraphs = response.split("\n\n")
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("There is no single answer to the meaning of life")
    assert "A person may find it in raising a child" in paragraphs[1]
    assert "uncertainty makes life meaningless" in paragraphs[2]
    assert "What detail or context" not in response
    assert "I won't invent" not in response
    assert result["doorway_title"] == ""


def test_existential_recovery_covers_clear_paraphrases_without_becoming_a_canned_general_answer():
    for query in (
        "What is the purpose of life?",
        "What's the meaning of life?",
        "What gives life meaning?",
        "Why are we here?",
        "What does it mean to live a meaningful life?",
    ):
        assert guide._is_broad_existential_question(query), query

    for query in (
        "What is the meaning of life in the Living Archive?",
        "What are the Living Archive's principles about purpose?",
        "I feel empty and see no reason to live.",
        "What is the best way to govern a community?",
        "What is the meaning of reciprocity?",
    ):
        assert not guide._is_broad_existential_question(query), query


def test_existential_recovery_does_not_override_exact_approved_standards():
    approved_query = "What are first principles, and what are the Living Archive’s first principles?"
    exact = guide.compose(use_core=None, query=approved_query, context_data={})
    assert exact is not None
    assert exact["provider"] == "gold_standard_registry"
    assert len(exact["response"].split("\n\n")) == 3


def test_existential_recovery_is_provider_independent_and_has_no_unverified_doorway():
    result = guide._broad_existential_recovery()
    assert result["provider"] == "bounded_existential_general_knowledge_recovery"
    assert result["doorway_title"] == ""
    assert result["response_shape"] == "explanatory"
    assert len(result["response"].split("\n\n")) == 3
    assert "The Living Archive says" not in result["response"]


def test_deterministic_provider_exhaustion_path_preserves_existential_answer_first_contract():
    result = main._basic_inquiry_round1_deterministic_response(
        "What is the meaning of life?",
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )

    assert result["provider"] == "bounded_existential_general_knowledge_recovery"
    assert len(result["response"].split("\\n\\n")) == 3
    assert result["doorway_title"] == ""
