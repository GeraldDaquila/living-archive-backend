"""Safety and end-to-end tests for the in-memory HRN pipeline simulation."""
import json

from hrn_deterministic_provider_prototype import reason
from hrn_pipeline_simulation import SimulatedHRNPipeline, scripted_provider


MESSAGES = [
    "I keep initiating contact with a friend, and I want to understand what is happening between us.",
    "Lately, they have been aloof, even ghosting my texts without explanation. I noticed this behavioral change last when I declined loaning them some money.",
    "The long silence, evaded answers, and as mentioned ghosting my texts. Since there's no clear cut time as to when this behavior started, I keep wondering as to what triggered it.",
]


def snapshot(turn, message, **overrides):
    data = {
        "request_id": f"request-{turn}",
        "session_id": "simulation-session",
        "visitor_turn_id": f"turn-{turn}",
        "turn_number": turn,
        "visitor_message": message,
    }
    data.update(overrides)
    return data


def prototype_provider(snap):
    return reason({
        **snap,
        "prior_moves": snap["committed_ledger"]["moves"],
        "prior_questions": snap["committed_ledger"]["questions"],
        "prior_responses": snap["committed_ledger"]["responses"],
    })


def test_three_turn_e2e_simulation_progresses_and_preserves_one_session():
    pipeline = SimulatedHRNPipeline(prototype_provider, prototype_provider)
    results = [pipeline.process(snapshot(i, message)) for i, message in enumerate(MESSAGES, 1)]

    assert all(result["status"] == "success" and result["committed"] for result in results)
    assert [result["turn_number"] for result in results] == [1, 2, 3]
    assert len({result["session_id"] for result in results}) == 1
    assert len({result["response"] for result in results}) == 3
    assert results[1]["provider_id"] == "primary"
    assert "timing" in results[1]["response"].casefold()
    assert "willing to talk" in results[2]["response"].casefold()
    ledger = pipeline.ledgers["simulation-session"]
    assert ledger["turn_number"] == 3
    assert [item["turn_id"] for item in ledger["visitor_evidence"]] == ["turn-1", "turn-2", "turn-3"]
    assert pipeline.commit_count == 3


def test_provider_failure_uses_same_snapshot_for_fallback_and_commits_once():
    seen = []

    def failing_primary(snap):
        seen.append(("primary", snap["session_id"], snap["visitor_turn_id"],
                     snap["current_evidence_delta"]["visitor_message_sha256"],
                     snap["committed_ledger"]["turn_number"]))
        raise TimeoutError("simulated provider timeout")

    def recovering_fallback(snap):
        seen.append(("fallback", snap["session_id"], snap["visitor_turn_id"],
                     snap["current_evidence_delta"]["visitor_message_sha256"],
                     snap["committed_ledger"]["turn_number"]))
        return scripted_provider("distinguish", "The timing stands out, but it does not establish cause.", "loan_decision_timing")(snap)

    pipeline = SimulatedHRNPipeline(failing_primary, recovering_fallback)
    result = pipeline.process(snapshot(1, MESSAGES[0]))
    assert result["status"] == "success"
    assert result["provider_id"] == "fallback"
    assert seen[0][1:] == seen[1][1:]
    assert result["turn_number"] == 1
    assert pipeline.commit_count == 1
    assert pipeline.ledgers["simulation-session"]["turn_number"] == 1


def test_malformed_primary_result_falls_back_without_partial_commit():
    pipeline = SimulatedHRNPipeline(
        lambda snap: {"status": "success", "response_draft": "missing required fields"},
        scripted_provider("clarify", "Let's begin with what changed in the friendship.", "relationship_distance"),
    )
    result = pipeline.process(snapshot(1, MESSAGES[0]))
    assert result["status"] == "success"
    assert result["provider_id"] == "fallback"
    assert pipeline.commit_count == 1
    assert pipeline.ledgers["simulation-session"]["turn_number"] == 1


def test_scripted_provider_echoes_request_identity():
    provider = scripted_provider("clarify", "A valid response.", "evidence",
                                 question="What would clarify this?")
    result = provider(snapshot(1, MESSAGES[0]))
    assert result["request_id"] == "request-1"


def test_wrong_request_identity_or_missing_question_is_rejected_before_commit():
    pipeline = SimulatedHRNPipeline(
        lambda snap: {
            **scripted_provider("clarify", "A response for the wrong request.", "evidence",
                                question="What would clarify this?")(snap),
            "request_id": "another-request",
        },
        scripted_provider("clarify", "A valid fallback response.", "evidence",
                          question="What would help clarify this?"),
    )
    first = pipeline.process(snapshot(1, MESSAGES[0]))
    assert first["status"] == "success"
    assert first["provider_id"] == "fallback"
    assert pipeline.commit_count == 1

    pipeline.primary = lambda snap: {**scripted_provider("clarify", "A response with no next question.", "evidence-2")(snap), "question": ""}
    pipeline.fallback = lambda snap: {**scripted_provider("clarify", "Fallback with no next question.", "evidence-2")(snap), "question": ""}
    second = pipeline.process(snapshot(2, MESSAGES[1]))
    assert second == {"status": "retryable_failure", "committed": False, "reason": "no_valid_result"}
    assert pipeline.ledgers["simulation-session"]["turn_number"] == 1
    assert pipeline.commit_count == 1


def test_repeated_response_from_both_providers_is_refused_without_commit():
    same = "We do not have to settle on an explanation yet. What do you notice?"
    primary = scripted_provider("clarify", same, "current_evidence")
    fallback = scripted_provider("clarify", same.upper().replace(" ", "  "), "current_evidence")
    pipeline = SimulatedHRNPipeline(primary, fallback)
    pipeline.process(snapshot(1, MESSAGES[0]))
    result = pipeline.process(snapshot(2, MESSAGES[1]))
    assert result == {"status": "retryable_failure", "committed": False, "reason": "no_valid_result"}
    assert pipeline.commit_count == 1
    assert pipeline.ledgers["simulation-session"]["turn_number"] == 1
    assert pipeline.ledgers["simulation-session"]["pending_visitor_evidence"]["turn_id"] == "turn-2"



def test_novel_response_with_repeated_question_is_refused_without_commit():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A first, concrete observation.", "evidence-1",
                          question="What do you notice when this happens?"),
        scripted_provider("clarify", "A fallback first-turn observation.", "evidence-1",
                          question="What else do you notice?"),
    )
    first = pipeline.process(snapshot(1, MESSAGES[0]))
    assert first["status"] == "success"

    pipeline.primary = scripted_provider(
        "deepen", "A new response, but the same question.", "evidence-2",
        question="What do you notice when this happens?",
    )
    pipeline.fallback = scripted_provider(
        "deepen", "A different fallback, but still the same question.", "evidence-2",
        question="What do you notice when this happens?",
    )
    second = pipeline.process(snapshot(2, MESSAGES[1]))
    assert second == {"status": "retryable_failure", "committed": False, "reason": "no_valid_result"}
    ledger = pipeline.ledgers["simulation-session"]
    assert ledger["turn_number"] == 1
    assert ledger["questions"] == ["What do you notice when this happens?"]
    assert ledger["pending_visitor_evidence"]["turn_id"] == "turn-2"
    assert pipeline.commit_count == 1

def test_duplicate_submission_is_idempotent_and_does_not_commit_twice():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A fresh, supported observation.", "evidence"),
        scripted_provider("clarify", "A fallback observation.", "evidence"),
    )
    request = snapshot(1, MESSAGES[0])
    first = pipeline.process(request)
    replay = pipeline.process(request)
    assert replay == first
    assert pipeline.commit_count == 1
    assert pipeline.ledgers["simulation-session"]["turn_number"] == 1


def test_out_of_order_turn_is_rejected_without_mutating_ledger():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A fresh, supported observation.", "evidence"),
        scripted_provider("clarify", "A fallback observation.", "evidence"),
    )
    result = pipeline.process(snapshot(2, MESSAGES[1]))
    assert result["status"] == "retryable_failure"
    assert result["reason"] == "turn_conflict"
    assert pipeline.commit_count == 0
    assert pipeline.ledgers == {}


def test_provider_cannot_change_session_or_turn_identity():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A response with the wrong session.", "evidence",
                          session_override="leaked-other-session"),
        scripted_provider("clarify", "A response within the original session.", "evidence"),
    )
    result = pipeline.process(snapshot(1, MESSAGES[0]))
    assert result["status"] == "success"
    assert result["provider_id"] == "fallback"
    assert result["session_id"] == "simulation-session"
    assert "leaked-other-session" not in json.dumps(pipeline.ledgers)


def test_provider_proposed_ledger_delta_is_never_authoritative():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "Only the shared pipeline commits state.", "evidence"),
        scripted_provider("clarify", "Fallback.", "evidence"),
    )
    result = pipeline.process(snapshot(1, MESSAGES[0]))
    ledger = pipeline.ledgers["simulation-session"]
    assert result["turn_number"] == 1
    assert ledger["turn_number"] == 1
    assert ledger["session_id"] == "simulation-session"
    assert "provider-must-not-own-commit" not in json.dumps(ledger)


def test_logs_never_contain_visitor_text_or_secret_like_values():
    private_text = "PRIVATE_VISITOR_TEXT_93A1 should not appear in telemetry"
    secret = "sk-test-secret-never-log"
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A safe, abstract observation.", "evidence"),
        scripted_provider("clarify", "Fallback observation.", "evidence"),
    )
    pipeline.process(snapshot(1, private_text, api_key=secret, provider_secret=secret))
    rendered = json.dumps(pipeline.events)
    assert private_text not in rendered
    assert secret not in rendered
    assert all("visitor_message" not in event for event in pipeline.events)
    assert all("api_key" not in event and "provider_secret" not in event for event in pipeline.events)
    assert all("session_id" not in event and "request_id" not in event and "turn_id" not in event for event in pipeline.events)
    assert "simulation-session" not in rendered


def test_provider_input_mutation_does_not_mutate_staged_or_committed_state():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A safe response after attempted mutation.", "evidence", mutate_input=True),
        scripted_provider("clarify", "Fallback after mutation.", "evidence"),
    )
    result = pipeline.process(snapshot(1, MESSAGES[0]))
    assert result["status"] == "success"
    assert result["provider_id"] == "primary"
    assert pipeline.ledgers["simulation-session"]["turn_number"] == 1


def test_closure_is_committed_once_and_replay_does_not_reopen_it():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("close", "We can leave this here without forcing an answer.", "closure_evidence"),
        scripted_provider("close", "A safe closure.", "closure_evidence"),
    )
    request = snapshot(1, "I would like to stop here.")
    result = pipeline.process(request)
    replay = pipeline.process(request)
    assert result["closed"] is True
    assert replay["closed"] is True
    assert pipeline.ledgers["simulation-session"]["closed"] is True
    assert pipeline.commit_count == 1


def test_new_turn_cannot_reopen_a_closed_journey():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("close", "We can leave this here without forcing an answer.", "closure_evidence"),
        scripted_provider("close", "A safe closure.", "closure_evidence"),
    )
    closed = pipeline.process(snapshot(1, "I would like to stop here."))
    assert closed["status"] == "success" and closed["closed"] is True

    after_close = pipeline.process(snapshot(2, "Actually, one more thing."))
    assert after_close == {"status": "retryable_failure", "committed": False, "reason": "journey_closed"}
    ledger = pipeline.ledgers["simulation-session"]
    assert ledger["turn_number"] == 1
    assert ledger["closed"] is True
    assert pipeline.commit_count == 1


def test_new_session_is_isolated_from_previous_session_state():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A response for this new session.", "evidence"),
        scripted_provider("clarify", "Fallback.", "evidence"),
    )
    first = pipeline.process(snapshot(1, MESSAGES[0], session_id="session-A"))
    second = pipeline.process(snapshot(1, MESSAGES[0], session_id="session-B"))
    assert first["status"] == second["status"] == "success"
    assert set(pipeline.ledgers) == {"session-A", "session-B"}
    assert pipeline.ledgers["session-A"]["turn_number"] == 1
    assert pipeline.ledgers["session-B"]["turn_number"] == 1


def test_failed_turn_preserves_committed_state_and_can_retry_same_turn():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A first-turn observation.", "relationship_distance"),
        scripted_provider("clarify", "A first-turn fallback.", "relationship_distance"),
    )
    first = pipeline.process(snapshot(1, MESSAGES[0]))
    assert first["status"] == "success"
    before = dict(pipeline.ledgers["simulation-session"])
    pipeline.primary = lambda snap: {"status": "failure"}
    pipeline.fallback = lambda snap: {"status": "insufficient_context"}
    failed = pipeline.process(snapshot(2, MESSAGES[1]))
    assert failed["status"] == "retryable_failure"
    after_failure = pipeline.ledgers["simulation-session"]
    assert after_failure["turn_number"] == before["turn_number"]
    assert after_failure["responses"] == before["responses"]
    assert after_failure["pending_visitor_evidence"]["turn_id"] == "turn-2"
    pipeline.primary = scripted_provider("distinguish", "The timing is relevant but not proof.", "loan_timing")
    retried = pipeline.process(snapshot(2, MESSAGES[1], request_id="request-2-retry"))
    assert retried["status"] == "success"
    assert retried["turn_number"] == 2
    assert pipeline.ledgers["simulation-session"]["pending_visitor_evidence"] is None
    assert pipeline.commit_count == 2
