"""Tests for task-sensitive illustrative grounding in social-mechanism explanations."""

import json

import pytest

import general_guide_composition as guide


QUESTION = "How do myths, symbols, and stories organize collective life?"


def test_collective_life_mechanism_question_requires_a_concrete_example():
    assert guide._requires_grounded_mechanism_example(QUESTION)


@pytest.mark.parametrize(
    "question",
    [
        "What is a myth?",
        "How do I organize my daily schedule?",
        "Why do stories matter?",
        "How do communities change over time?",
    ],
)
def test_example_requirement_does_not_spread_to_unrelated_questions(question):
    assert not guide._requires_grounded_mechanism_example(question)


def test_developed_illustration_demonstrates_the_mechanism():
    response = (
        "Shared stories and symbols organize collective life by making expectations and belonging "
        "visible, memorable, and emotionally meaningful. They can establish who is included, what "
        "conduct is admired, and which obligations feel legitimate. For example, a national flag "
        "can remind people that they belong to a political community larger than their household; "
        "at a public ceremony, that symbol coordinates attention and expresses a shared commitment. "
        "The effect is not automatic: people may interpret the same symbol differently or reject "
        "the story attached to it."
    )
    assert guide._has_grounded_illustrative_example(response)


def test_decorative_example_marker_without_mechanism_is_rejected():
    response = (
        "For example, a flag is an object that people may see at different times. "
        "It can be found in many places and has different colors and shapes."
    )
    assert not guide._has_grounded_illustrative_example(response)


def test_parser_rejects_abstract_only_collective_life_mechanism_answer():
    response = (
        "Myths, symbols, and stories organize collective life by shaping shared expectations, "
        "relationships, and ideas about belonging. Repeated narratives can make some choices "
        "seem normal, admirable, or difficult to question. They influence how people understand "
        "their roles and how communities coordinate behavior."
    )
    parse = guide._parse_factory([], query=QUESTION, emit_telemetry=False)
    with pytest.raises(ValueError, match="must include one concrete illustrative example"):
        parse(json.dumps({"response": response}))


def test_parser_accepts_mechanism_explanation_with_bounded_illustration():
    response = (
        "Myths, symbols, and stories organize collective life by making shared expectations, "
        "belonging, and authority visible and memorable. They help people interpret who belongs "
        "and which obligations are treated as legitimate. For example, a national flag can remind "
        "people that they belong to a political community larger than their household; at a public "
        "ceremony, the symbol coordinates attention and expresses a shared commitment. The effect "
        "is not automatic, because people can interpret the same symbol differently or reject the "
        "story attached to it."
    )
    parse = guide._parse_factory([], query=QUESTION, emit_telemetry=False)
    result = parse(json.dumps({"response": response}))
    assert result["response"] == response
