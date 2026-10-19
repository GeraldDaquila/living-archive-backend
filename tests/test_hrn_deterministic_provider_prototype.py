"""Acceptance tests for the isolated HRN deterministic reasoning prototype."""
from copy import deepcopy

from hrn_deterministic_provider_prototype import reason


def _snapshot(turn, message, **overrides):
    value = {
        "contract_version": "hrn-reasoning-input/0.1",
        "request_id": "req-fixed",
        "session_id": "session-fixed",
        "visitor_turn_id": f"turn-{turn}",
        "turn_number": turn,
        "visitor_message": message,
        "committed_ledger": {"turn_number": turn - 1},
        "known_observations": [],
        "prior_questions": [],
        "prior_moves": [],
        "allowed_moves": ["clarify", "distinguish", "deepen", "reflect", "close"],
    }
    value.update(overrides)
    return value


def test_first_turn_starts_with_observable_behavior():
    result = reason(_snapshot(
        1,
        "I keep initiating contact with a friend, and I want to understand what is happening between us.",
    ))
    assert result["status"] == "success"
    assert result["next_move"] == "clarify"
    assert "What has changed most noticeably" in result["response_draft"]
    assert result["session_id"] == "session-fixed"


def test_second_turn_acknowledges_loan_timing_without_claiming_causation():
    result = reason(_snapshot(
        2,
        "Lately, they have been aloof, even ghosting my texts without explanation. "
        "I noticed this behavioral change last when I declined loaning them some money.",
    ))
    assert result["status"] == "success"
    assert result["next_move"] == "distinguish"
    response = result["response_draft"].casefold()
    assert "timing" in response
    assert "cannot tell us whether that caused" in response
    assert "did your friend connect" in response
    assert "temporal_association_is_not_causation" in result["limitations"]


def test_third_turn_advances_from_trigger_to_willingness_to_engage():
    result = reason(_snapshot(
        3,
        "The long silence, evaded answers, and as mentioned ghosting my texts. "
        "Since there's no clear cut time as to when this behavior started, I keep wondering as to what triggered it.",
        prior_moves=["clarify", "distinguish"],
    ))
    assert result["status"] == "success"
    assert result["next_move"] == "deepen"
    response = result["response_draft"].casefold()
    assert "silence and evasive answers" in response
    assert "whether your friend is willing to talk" in response
    assert "how have they responded" in response
    assert "outside_supported_deterministic_scope" not in result["limitations"]


def test_unsupported_scenario_returns_limited_status_not_fake_success():
    result = reason(_snapshot(4, "My colleague has been acting strangely at work."))
    assert result["status"] == "insufficient_context"
    assert "outside_supported_deterministic_scope" in result["limitations"]


def test_provider_does_not_mutate_input_snapshot():
    snapshot = _snapshot(2, "I noticed this after I declined to lend them some money.")
    before = deepcopy(snapshot)
    reason(snapshot)
    assert snapshot == before


def test_session_and_turn_identity_are_preserved():
    result = reason(_snapshot(2, "I declined lending money and then my friend became aloof."))
    assert result["session_id"] == "session-fixed"
    assert result["visitor_turn_id"] == "turn-2"
    assert result["proposed_state_delta"]["turn_number"] == 2


def test_repeat_guard_does_not_silently_accept_a_repeated_question():
    message = "I declined lending money and then my friend became aloof."
    prior_response = reason(_snapshot(2, message))["response_draft"]
    result = reason(_snapshot(2, message, prior_questions=[prior_response]))
    assert result["status"] == "insufficient_context"
    assert "repetition_guard_triggered" in result["limitations"]



def test_third_turn_needs_prior_journey_state_to_advance():
    result = reason(_snapshot(
        3,
        "The long silence, evaded answers, and ghosting my texts leave me wondering what triggered it.",
    ))
    assert result["status"] == "insufficient_context"
    assert "outside_supported_deterministic_scope" in result["limitations"]



def test_three_turn_sequence_carries_provider_state_without_mutating_prior_results():
    session_id = "one-session-for-all-three-turns"
    prior_moves = []
    prior_questions = []
    messages = [
        "I keep initiating contact with a friend, and I want to understand what is happening between us.",
        "Lately, they have been aloof, even ghosting my texts without explanation. I noticed this behavioral change last when I declined loaning them some money.",
        "The long silence, evaded answers, and as mentioned ghosting my texts. Since there's no clear cut time as to when this behavior started, I keep wondering as to what triggered it.",
    ]
    results = []
    for turn, message in enumerate(messages, start=1):
        snapshot = _snapshot(
            turn,
            message,
            session_id=session_id,
            prior_moves=list(prior_moves),
            prior_questions=list(prior_questions),
            known_observations=[
                observation
                for prior in results
                for observation in prior["observations"]
            ],
        )
        result = reason(snapshot)
        results.append(result)
        assert result["session_id"] == session_id
        assert result["visitor_turn_id"] == f"turn-{turn}"
        assert result["status"] == "success"
        prior_moves.append(result["next_move"])
        prior_questions.append(result["response_draft"])

    assert [item["next_move"] for item in results] == ["clarify", "distinguish", "deepen"]
    assert len({item["response_draft"] for item in results}) == 3
    assert "timing" in results[1]["response_draft"].casefold()
    assert "willing to talk" in results[2]["response_draft"].casefold()



def test_repeated_response_is_not_accepted_as_progress_even_with_a_new_turn_id():
    message = (
        "The long silence, evaded answers, and ghosting my texts leave me "
        "wondering what triggered it."
    )
    repeated_response = (
        "We do not have to settle on an explanation yet. We can start with "
        "one concrete moment and look at what happened, without assuming "
        "what either person meant."
    )
    result = reason(_snapshot(
        3,
        message,
        prior_moves=["clarify", "distinguish"],
        prior_questions=["What is the first thing you notice when this situation begins to feel difficult?"],
        prior_responses=[repeated_response],
    ))
    assert result["status"] == "insufficient_context"
    assert "response_progression_guard_triggered" in result["limitations"]
    assert "cannot be committed as progress" in result["move_rationale"]


def test_response_progression_guard_ignores_whitespace_and_case_only_changes():
    message = (
        "The long silence, evaded answers, and ghosting my texts leave me "
        "wondering what triggered it."
    )
    repeated_response = (
        "WE DO NOT HAVE TO SETTLE ON AN EXPLANATION YET.  We can start with "
        "one concrete moment and look at what happened, without assuming "
        "what either person meant."
    )
    result = reason(_snapshot(
        3,
        message,
        prior_moves=["clarify", "distinguish"],
        prior_responses=[repeated_response],
    ))
    assert result["status"] == "insufficient_context"
    assert "response_progression_guard_triggered" in result["limitations"]
