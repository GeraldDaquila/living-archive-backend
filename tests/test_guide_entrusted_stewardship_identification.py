import pytest

from general_guide_composition import (
    _entrusted_stewardship_identification_recovery,
    _has_entrusted_stewardship_identification,
    _requires_entrusted_stewardship_identification,
    enforce_response_contracts,
)


QUESTION = "How does one identify what is being held in trust in a given situation?"


def test_recognizes_held_in_trust_identification_question_without_overcapturing():
    assert _requires_entrusted_stewardship_identification(QUESTION)
    assert not _requires_entrusted_stewardship_identification(
        "How can an organization build trust with its team?"
    )
    assert not _requires_entrusted_stewardship_identification(
        "What should I do next in a difficult situation?"
    )


def test_generic_action_planning_response_is_replaced_by_direct_explanation():
    generic = (
        "A practical way to approach one identify what is being held in trust in a given "
        "situation is to define the outcome you want, identify the main constraint, and "
        "choose one step small enough to test. Before acting, consider who else is affected "
        "and what could go wrong. Check the result against the original goal and adjust "
        "rather than assuming the first attempt must be final."
    )
    recovered = enforce_response_contracts(QUESTION, generic)
    assert recovered != generic
    assert _has_entrusted_stewardship_identification(recovered)
    assert len([p for p in recovered.split("\\n\\n") if p.strip()]) == 3
    for concept in (
        "what has been placed in someone's care",
        "who or what depends on that care",
        "obligations",
        "misuse or neglect",
        "authority ends",
    ):
        assert concept in recovered.casefold()


def test_recovery_meets_contract_and_is_three_paragraphs():
    answer = _entrusted_stewardship_identification_recovery()
    assert _has_entrusted_stewardship_identification(answer)
    assert len([p for p in answer.split("\\n\\n") if p.strip()]) == 3


def test_substantive_answer_passes_and_generic_one_fails():
    answer = _entrusted_stewardship_identification_recovery()
    assert enforce_response_contracts(QUESTION, answer) == answer
    assert not _has_entrusted_stewardship_identification(
        "Identify the outcome you want, consider who is affected, and choose one step."
    )
