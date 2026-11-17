"""Hard visitor-boundary tests for the Guide's default answer-first standard."""

import json

import pytest

import general_guide_composition as guide


QUESTION = (
    "A visitor asks how stewardship differs from management and ownership. "
    "What comparison structure would make the distinctions usable?"
)


def test_answer_first_gate_rejects_announced_comparison_and_echoed_question():
    response = (
        "A sound comparison of A visitor asks how stewardship differs from management "
        "and ownership begins by naming the options.\n\n"
        "Then compare how each option works and what consequences follow.\n\n"
        "The distinction matters because the roles can overlap without being interchangeable."
    )
    assert not guide._has_direct_answer_opening(QUESTION, response)


def test_answer_first_gate_accepts_a_substantive_opening():
    response = (
        "Ownership concerns rights and control, management concerns organizing work, "
        "and stewardship concerns responsibility for the long-term health of what is entrusted to someone's care.\n\n"
        "The roles can overlap: an owner may appoint a manager, while a steward considers whether "
        "the asset, people, and conditions entrusted to them remain healthy over time.\n\n"
        "A useful test is to ask who holds the rights, who directs the daily work, and who remains "
        "accountable for long-term consequences."
    )
    assert guide._has_direct_answer_opening(QUESTION, response)


def test_soft_contract_lane_cannot_admit_a_meta_opening():
    response = (
        "A sound comparison of A visitor asks how stewardship differs from management and ownership "
        "begins by naming the options.\n\n"
        "Then compare how each option works and what consequences follow.\n\n"
        "The distinction matters because the roles can overlap without being interchangeable."
    )
    payload = {
        "response": response,
        "doorway_title": "",
        "response_shape": "explanatory",
    }
    parser = guide._parse_factory([], QUESTION)
    with pytest.raises(ValueError, match="answer-first"):
        parser(json.dumps(payload))
