"""Regression tests for conceptual relationship questions in The Guide."""
import json
from pathlib import Path

import pytest
from general_guide_composition import (
    _conceptual_relationship_recovery,
    _has_transparency_trust_reciprocity,
    _build_general_guide_system_prompt,
    has_conceptual_relationship_explanation,
    is_conceptual_relationship_question,
)


RELATIONSHIP_QUESTION = (
    "How might accountability, trust, and the ability to repair harm "
    "reinforce one another?"
)
GENERIC_PRACTICAL_RESPONSE = (
    "A practical way to approach this is to define the outcome you want, "
    "identify the main constraint, and choose one step small enough to test. "
    "Before acting, consider who else is affected and what could go wrong. "
    "Check the result against the original goal and adjust rather than assuming "
    "the first attempt must be final. What detail or context would make this "
    "question most concrete for you?"
)


def test_accountability_trust_harm_question_is_classified_as_conceptual_relationship():
    assert is_conceptual_relationship_question(RELATIONSHIP_QUESTION)


def test_conceptual_relationship_paraphrases_are_classified():
    for query in (
        "How do accountability and trust strengthen each other?",
        "What is the relationship between repairing harm and rebuilding trust?",
        "How can responsibility and repair support one another?",
    ):
        assert is_conceptual_relationship_question(query)


def test_generic_problem_solving_response_fails_relationship_contract():
    assert not has_conceptual_relationship_explanation(GENERIC_PRACTICAL_RESPONSE)


def test_recovery_explains_the_mechanism_between_concepts():
    response = _conceptual_relationship_recovery(RELATIONSHIP_QUESTION)
    assert has_conceptual_relationship_explanation(response)
    assert "because people can judge" in response
    assert "repair turns accountability into action" in response.casefold()
    assert response.endswith("community?")


def test_conceptual_question_is_not_misclassified_as_practical_how_to():
    from general_guide_composition import is_practical_application_question

    assert not is_practical_application_question(RELATIONSHIP_QUESTION)


def test_explanatory_question_rejects_deliberative_template_contamination():
    from general_guide_composition import is_generic_nonanswer
    query = "How can developmental language become hierarchical or dismissive?"
    response = (
        "A practical way to approach this is by clarifying the outcome and the responsibilities involved.\n\n"
        "Next, compare a small number of realistic options and consider likely benefits, foreseeable harms, and who carries the costs.\n\n"
        "Finally, act on the best-supported option and review the consequences."
    )
    assert is_generic_nonanswer(query, response)


def test_developmental_language_gold_star_recovery_principle():
    from general_guide_composition import is_generic_nonanswer
    query = "How can developmental language become hierarchical or dismissive?"
    response = (
        "Developmental language can become hierarchical when descriptions of different capacities "
        "or patterns are treated as rankings of human worth. A framework becomes dismissive when "
        "a label explains away someone's perspective rather than engaging with what they are saying."
    )
    assert not is_generic_nonanswer(query, response)


def test_algorithmic_amplification_contract_names_mechanism_before_system_context():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    for phrase in (
        "how algorithmic or automated systems scale existing biases",
        "repeated ranking, allocation, recommendation, classification, optimization, or feedback loops",
        "Distinguish amplification from sole causation",
    ):
        assert phrase in source


TRANSPARENCY_TRUST_QUESTION = "What is the relationship between transparency and trust?"


def test_transparency_trust_is_recognized_as_a_conceptual_relationship():
    assert is_conceptual_relationship_question(TRANSPARENCY_TRUST_QUESTION)


def test_transparency_trust_has_a_bounded_answer_when_provider_composition_is_unavailable():
    from general_guide_composition import is_generic_nonanswer

    response = _conceptual_relationship_recovery(TRANSPARENCY_TRUST_QUESTION)
    assert response
    assert has_conceptual_relationship_explanation(response, TRANSPARENCY_TRUST_QUESTION)
    assert "visibility creates the possibility of scrutiny" in response.casefold()
    assert "neither side guarantees the other" in response
    assert "legitimate confidentiality" in response
    assert not is_generic_nonanswer(TRANSPARENCY_TRUST_QUESTION, response)


def test_transparency_trust_recovery_does_not_claim_archive_doctrine():
    response = _conceptual_relationship_recovery(TRANSPARENCY_TRUST_QUESTION)
    assert "not a claim that the Living Archive states a formal definition" in response


def test_transparency_trust_provider_answer_must_explain_reciprocity():
    one_way_answer = (
        "Transparency makes decisions visible and can support trust because people can inspect "
        "what an institution does. Trust can exist without transparency, so the relationship is "
        "one-way. People may rely on others for many reasons, and disclosure alone does not make "
        "conduct reliable. Institutions should protect confidential information while explaining "
        "their decisions and making evidence available for review."
    )
    reciprocal_answer = _conceptual_relationship_recovery(TRANSPARENCY_TRUST_QUESTION)

    assert not _has_transparency_trust_reciprocity(one_way_answer)
    assert _has_transparency_trust_reciprocity(reciprocal_answer)


def test_transparency_trust_prompt_requires_both_directions_and_non_guarantee():
    prompt = _build_general_guide_system_prompt(TRANSPARENCY_TRUST_QUESTION)

    assert "TRANSPARENCY AND TRUST RECIPROCITY" in prompt
    assert "explain both directions of influence" in prompt
    assert "Do not describe the relationship as one-way" in prompt


def test_provider_parser_rejects_one_way_transparency_trust_answer():
    from general_guide_composition import _parse_factory

    one_way_answer = (
        "Transparency makes decisions visible and can support trust because people can inspect "
        "what an institution does. Trust can exist without transparency, so the relationship is "
        "one-way. People may rely on others for many reasons, and disclosure alone does not make "
        "conduct reliable. Institutions should protect confidential information while explaining "
        "their decisions and making evidence available for review."
    )
    parse = _parse_factory([], query=TRANSPARENCY_TRUST_QUESTION, emit_telemetry=False)

    with pytest.raises(ValueError, match="transparency-trust answer must explain both directions"):
        parse(json.dumps({"response": one_way_answer}))


def test_transparency_trust_accepts_equivalent_reciprocal_mechanism_wording():
    response = (
        "Transparency supports justified trust because decisions and reasons can be inspected, "
        "questioned, and corrected. When people trust the process, they are more likely to share "
        "information, raise concerns, and take part candidly; institutions must respond honestly. "
        "Neither transparency nor trust guarantees the other: disclosure cannot make harmful conduct "
        "trustworthy, and trust cannot replace accountability."
    )
    assert _has_transparency_trust_reciprocity(response)


def test_transparency_trust_still_rejects_reciprocity_without_a_non_guarantee_boundary():
    response = (
        "Transparency supports trust by making decisions open to scrutiny. Trust encourages people "
        "to share information and raise concerns, and institutions should respond candidly."
    )
    assert not _has_transparency_trust_reciprocity(response)
