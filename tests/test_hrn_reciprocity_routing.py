"""Regression tests for natural HRN specialist routing."""

import main


def test_friendship_uneven_effort_question_routes_to_hrn():
    question = (
        "I care about a friend, but lately I feel I'm always the one making "
        "an effort. I don't want to judge them unfairly, but I also don't "
        "want to keep ignoring how I feel. How can I understand what's "
        "happening between us?"
    )
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_bounded_resource_lookup_does_not_route_to_hrn():
    question = "Where can I find material about institutional responsibility?"
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is False
    assert decision["reason"] == "bounded_archive_or_definition_request"



def test_lived_workplace_credit_taking_question_routes_to_hrn():
    question = (
        "I feel frustrated because my colleague keeps taking credit for work we did together. "
        "What might I be missing about the relationship?"
    )
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_lived_workplace_credit_omission_routes_to_hrn():
    question = (
        "My teammate presented our project results without mentioning my contribution. "
        "What might I be missing about the relationship?"
    )
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_generic_workplace_credit_taking_question_stays_outside_hrn():
    question = "What are common patterns of taking credit in workplace relationships?"
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is False
    assert decision["reason"] == "insufficient_converging_relational_evidence"
