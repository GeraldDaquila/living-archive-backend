import json

import pytest

from community_rule_decision_contract import (
    evaluate_community_rule_response,
    is_community_rule_decision_question,
    build_community_rule_decision_instruction,
)
from general_guide_composition import _parse_factory


QUESTION = (
    "How should a community decide whether limits on personal liberty are justified "
    "by shared obligations and risks?"
)

INCOMPLETE = (
    "A community can decide whether limits on personal liberty are justified by "
    "working through a disciplined set of questions rather than relying on majority "
    "preference alone. The following framework gives each limit a fair test and keeps "
    "the decision answerable to the people it affects."
)

COMPLETE = (
    "A rule needs a legitimate shared purpose and demonstrable harm, not simply a "
    "majority preference. Test whether the restriction is necessary and proportionate, and whether "
    "a less restrictive workable alternative could address the shared need.\n\n"
    "Identify who benefits, who bears the costs, and whose liberty is restricted so the "
    "burden is allocated fairly. Provide reasonable accommodation for people whose "
    "circumstances or needs differ. People most affected should have a meaningful "
    "opportunity to shape the rule before it is adopted, not merely appeal afterward. "
    "Provide a route to appeal or challenge its application and observable criteria for "
    "reviewing whether the rule remains necessary and fair."
)


def test_community_rule_contract_requires_all_six_decision_dimensions():
    report = evaluate_community_rule_response(QUESTION, COMPLETE)
    assert report["applies"] is True
    assert report["passed"] is True
    assert report["missing"] == []


def test_community_rule_contract_rejects_framework_only_answer():
    report = evaluate_community_rule_response(QUESTION, INCOMPLETE)
    assert report["applies"] is True
    assert report["passed"] is False
    assert set(report["missing"]) == {
        "legitimate_shared_purpose",
        "necessity_and_least_restrictive_means",
        "fair_burden_allocation",
        "reasonable_accommodation",
        "affected_party_participation",
        "appeal_and_review",
    }


def test_community_rule_contract_rejects_majority_as_sufficient_authority():
    answer = COMPLETE + " A majority alone is entitled to restrict personal liberty."
    report = evaluate_community_rule_response(QUESTION, answer)
    assert report["passed"] is False
    assert report["majority_only"] is True
    assert "majority_preference_not_sufficient" in report["missing"]


def test_provider_parser_rejects_incomplete_community_rule_candidate():
    parse = _parse_factory([], QUESTION, None)
    raw = json.dumps({
        "response": INCOMPLETE,
        "doorway_title": "",
        "response_shape": "explanatory",
    })
    with pytest.raises(ValueError, match="community liberty-limit answer is incomplete"):
        parse(raw)


def test_provider_parser_accepts_complete_community_rule_candidate():
    parse = _parse_factory([], QUESTION, None)
    raw = json.dumps({
        "response": COMPLETE,
        "doorway_title": "",
        "response_shape": "explanatory",
    })
    parsed = parse(raw)
    assert parsed["response"] == COMPLETE



def test_community_rule_instruction_makes_all_six_dimensions_explicit_without_checklist_style():
    instruction = build_community_rule_decision_instruction()
    for phrase in (
        "legitimate shared purpose",
        "less restrictive workable means",
        "who benefits",
        "who bears costs",
        "reasonable accommodation",
        "fair burden allocation",
        "People most affected should have a meaningful opportunity to shape the rule before adoption",
        "later appeal alone does not substitute for participation",
        "appeal and review criteria",
        "Treat each as distinct evidence",
        "Use prose",
    ):
        assert phrase in instruction


def test_valid_provider_answer_survives_shared_final_contract_for_ethical_tradeoff():
    from general_guide_composition import enforce_response_contracts

    question = (
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both fair and workable?"
    )
    report = evaluate_community_rule_response(question, COMPLETE)
    assert report["applies"] is True
    assert report["passed"] is True

    # A candidate already accepted by the strict community-rule contract must
    # pass through unchanged; the deterministic recovery is not a replacement
    # for a provider answer that met every required dimension.
    assert enforce_response_contracts(question, COMPLETE) == COMPLETE


def test_incomplete_provider_answer_still_uses_registered_ethical_tradeoff_recovery():
    from deterministic_answer_recovery import compose_recovery
    from general_guide_composition import enforce_response_contracts

    question = (
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both fair and workable?"
    )
    assert evaluate_community_rule_response(question, INCOMPLETE)["passed"] is False

    recovered = enforce_response_contracts(question, INCOMPLETE)
    assert recovered == compose_recovery(question)
    assert evaluate_community_rule_response(question, recovered)["passed"] is True


def test_majority_only_provider_answer_cannot_bypass_community_rule_recovery():
    from general_guide_composition import enforce_response_contracts

    question = (
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both fair and workable?"
    )
    majority_only = COMPLETE + " A majority alone is entitled to restrict individual freedom."
    assert evaluate_community_rule_response(question, majority_only)["passed"] is False

    recovered = enforce_response_contracts(question, majority_only)
    assert recovered != majority_only
    assert evaluate_community_rule_response(question, recovered)["passed"] is True
