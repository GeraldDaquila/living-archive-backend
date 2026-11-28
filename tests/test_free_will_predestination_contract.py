"""Regression tests for free-will/predestination conceptual precision."""

import json

import pytest

import free_will_predestination_contract as contract
import general_guide_composition as composition


QUESTION = (
    "How do you reconcile free will with predestination: are people "
    "programmed to behave a certain way?"
)

WEAK_SCREENSHOT_ANSWER = (
    "Free will and predestination are not usually reconciled by saying people are simply "
    "programmed. The two ideas describe different levels of explanation, and whether they "
    "can coexist depends on which framework you are using and how you define each term. "
    "Predestination generally means that outcomes are fixed in advance by a divine will, "
    "fate, or causal necessity. Free will generally means that a person can genuinely choose "
    "among alternatives and be responsible for those choices. If predestination is absolute "
    "and every action is fixed before it happens, then free will in the strong sense—being "
    "able to do otherwise in the exact same circumstances—does not survive.\n\n"
    "But many traditions hold that the two can coexist, and they do so in different ways. "
    "Some argue that divine foreknowledge is not the same as divine causation: knowing what "
    "someone will choose does not force them to choose it. Others say that God or fate ordains "
    "the ends but leaves the means to human choice, or that human actions are both freely "
    "chosen and part of a larger providential order. A third view treats predestination as "
    "complete and does not identify human will, holding that people act according to their "
    "nature and circumstances while still being morally accountable in some qualified sense. "
    "Whether people are 'programmed' depends on which account you accept. If behavior is fully "
    "determined by prior causes, biology, or divine decree, then meaningful choice may be "
    "conditioned or programmed, even if they experience their choices as free. If choice is "
    "real and not fully fixed in advance, then people are not programmed, and they are still "
    "shaped by inheritance, upbringing, and context. There is no single philosophical or "
    "theological consensus on which view is correct, so the honest answer is that the "
    "reconciliation depends on the framework you adopt and how strongly you define free will."
)


def test_question_recognition_requires_the_actual_free_will_determination_relationship():
    assert contract.is_free_will_predestination_question(QUESTION)
    assert contract.is_free_will_predestination_question(
        "Can free choice coexist with causal determinism?"
    )
    assert contract.is_free_will_predestination_question(
        "Is human agency compatible with predetermination?"
    )


@pytest.mark.parametrize(
    "question",
    [
        "What does free will mean?",
        "What is predestination in Christian theology?",
        "How does upbringing shape a person's choices?",
        "Can people change their habits?",
        "What is the difference between coercion and persuasion?",
    ],
)
def test_unrelated_agency_theology_and_causation_questions_are_negative_controls(question):
    assert not contract.is_free_will_predestination_question(question)


def test_structured_recovery_meets_every_required_reasoning_distinction():
    answer = contract.free_will_predestination_recovery()
    assert contract.has_free_will_predestination_explanation(answer)


def test_original_screenshot_answer_is_preserved_but_fails_the_new_precision_gate():
    assert not contract.has_free_will_predestination_explanation(WEAK_SCREENSHOT_ANSWER)


def test_provider_parser_rejects_a_fluent_but_conceptually_incomplete_answer():
    parse = composition._parse_factory([], query=QUESTION, emit_telemetry=False)
    with pytest.raises(ValueError, match="free-will/predestination answer must distinguish"):
        parse(json.dumps({"response": WEAK_SCREENSHOT_ANSWER}))


def test_provider_parser_accepts_a_complete_balanced_answer():
    parse = composition._parse_factory([], query=QUESTION, emit_telemetry=False)
    answer = contract.free_will_predestination_recovery()
    assert parse(json.dumps({"response": answer}))["response"] == answer


def test_final_response_boundary_repairs_only_an_incomplete_answer():
    answer = contract.free_will_predestination_recovery()
    assert composition.enforce_response_contracts(QUESTION, WEAK_SCREENSHOT_ANSWER) == answer
    assert composition.enforce_response_contracts(QUESTION, answer) == answer


def test_question_specific_prompt_is_attached_only_to_this_relationship_family():
    prompt = composition._build_general_guide_system_prompt(QUESTION)
    assert "FREE WILL, PREDESTINATION, AND DETERMINISM" in prompt
    assert "compatibilism is one philosophical account" in prompt.casefold()

    unrelated = composition._build_general_guide_system_prompt("What does free will mean?")
    assert "FREE WILL, PREDESTINATION, AND DETERMINISM" not in unrelated
