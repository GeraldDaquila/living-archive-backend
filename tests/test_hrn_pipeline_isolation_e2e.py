"""Additional isolation and idempotency-boundary E2E tests for simulated HRN."""
from copy import deepcopy

from hrn_pipeline_simulation import SimulatedHRNPipeline, scripted_provider


def _snapshot(session, turn, message, request=None):
    return {
        "request_id": request or f"req-{session}-{turn}",
        "session_id": session,
        "visitor_turn_id": f"turn-{turn}",
        "turn_number": turn,
        "visitor_message": message,
    }


def test_interleaved_sessions_do_not_share_turns_responses_or_evidence():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A response for this session.", "session_evidence"),
        scripted_provider("clarify", "Fallback response for this session.", "session_evidence"),
    )

    a1 = pipeline.process(_snapshot("A", 1, "I am thinking about a friendship."))
    b1 = pipeline.process(_snapshot("B", 1, "I am thinking about a workplace issue."))
    a2 = pipeline.process(_snapshot("A", 2, "The silence began after a disagreement."))

    assert [a1["turn_number"], b1["turn_number"], a2["turn_number"]] == [1, 1, 2]
    assert set(pipeline.ledgers) == {"A", "B"}
    assert pipeline.ledgers["A"]["turn_number"] == 2
    assert pipeline.ledgers["B"]["turn_number"] == 1
    assert len(pipeline.ledgers["A"]["visitor_evidence"]) == 2
    assert len(pipeline.ledgers["B"]["visitor_evidence"]) == 1
    assert len(pipeline.ledgers["A"]["responses"]) == 2
    assert len(pipeline.ledgers["B"]["responses"]) == 1


def test_retry_of_failed_turn_does_not_mutate_another_session():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A first response.", "first_evidence"),
        scripted_provider("clarify", "A fallback response.", "first_evidence"),
    )
    pipeline.process(_snapshot("A", 1, "First session opening."))
    pipeline.process(_snapshot("B", 1, "Second session opening."))
    before_b = deepcopy(pipeline.ledgers["B"])

    pipeline.primary = lambda snap: {"status": "failure"}
    pipeline.fallback = lambda snap: {"status": "insufficient_context"}
    failed = pipeline.process(_snapshot("A", 2, "New evidence in session A."))

    assert failed["status"] == "retryable_failure"
    assert pipeline.ledgers["B"] == before_b
    assert pipeline.ledgers["A"]["turn_number"] == 1
    assert pipeline.ledgers["A"]["pending_visitor_evidence"]["turn_id"] == "turn-2"


def test_replay_with_same_turn_id_but_different_message_is_not_silently_accepted():
    pipeline = SimulatedHRNPipeline(
        scripted_provider("clarify", "A grounded first response.", "first_evidence"),
        scripted_provider("clarify", "A fallback response.", "first_evidence"),
    )
    original = _snapshot("A", 1, "The friendship feels distant.")
    first = pipeline.process(original)
    assert first["status"] == "success"

    altered = _snapshot("A", 1, "Actually this is about my employer.", request="new-request-id")
    result = pipeline.process(altered)

    assert result["status"] == "retryable_failure"
    assert result["committed"] is False
    assert result["reason"] == "idempotency_conflict"
    assert pipeline.commit_count == 1
    assert pipeline.ledgers["A"]["turn_number"] == 1
    assert pipeline.ledgers["A"]["visitor_evidence"][0]["message_sha256"] != (
        pipeline.ledgers["A"]["pending_visitor_evidence"]["message_sha256"]
        if pipeline.ledgers["A"]["pending_visitor_evidence"] else ""
    )
