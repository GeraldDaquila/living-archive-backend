import json

import pytest

from community_rule_decision_contract import (
    evaluate_community_rule_response,
    is_community_rule_decision_question,
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
    "majority preference. Test whether the restriction is necessary and proportionate, "
    "and whether a less restrictive workable alternative could address the shared need. "
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
