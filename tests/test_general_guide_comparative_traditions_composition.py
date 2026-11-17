import json

import pytest

import comparative_traditions_contract as traditions
import general_guide_composition as composition


QUESTION = "How can multiple spiritual traditions be approached with respect and intellectual discipline?"


def _candidate(response):
    return json.dumps({
        "response": response,
        "doorway_title": "",
        "response_shape": "explanatory",
    })


def test_provider_parser_rejects_institutional_substitution():
    off_topic = (
        "The inquiry begins by making the situation itself visible: multiple spiritual traditions "
        "are approached with respect and intellectual discipline. What outcome is the organisation "
        "trying to achieve, what responsibilities does it carry, and who will live with the consequences? "
        "Those questions bring operations, governance, human development, ethics, and stewardship into the same frame.\n\n"
        "From there, compare the real options rather than assuming that the proposed course is the only one. "
        "Look at what each option makes possible, what it may damage, who bears the costs, and what evidence "
        "would justify changing direction.\n\n"
        "The point is not to make the decision for the organisation, but to make the grounds for acting clearer."
    )
    parser = composition._parse_factory([], QUESTION)
    with pytest.raises(ValueError, match="comparative-traditions answer"):
        parser(_candidate(off_topic))


def test_provider_parser_accepts_substantive_comparative_recovery():
    response = traditions.recovery_response()
    parser = composition._parse_factory([], QUESTION)
    parsed = parser(_candidate(response))
    assert parsed["response"] == response


def test_provider_exhaustion_recovery_returns_answer_and_verified_doorway():
    result = composition._comparative_traditions_recovery(QUESTION)
    assert result is not None
    assert result["provider"] == "bounded_comparative_traditions_recovery"
    assert len(result["response"].split("\\n\\n")) == 3
    assert result["doorway_title"] == "At the Edge of Explanation"
    assert result["doorway_url"] == "https://geralddaquila.com/2026/07/20/at-the-edge-of-explanation/"


def test_provider_exhaustion_recovery_does_not_trigger_for_unrelated_question():
    assert composition._comparative_traditions_recovery(
        "How should an organisation redesign governance?"
    ) is None
