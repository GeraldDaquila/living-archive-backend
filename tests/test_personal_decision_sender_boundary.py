"""The shared JSON sender must enforce the registered personal-agency contract."""

import asyncio
import json


QUERY = (
    "A user asks for a personal life decision to be made for them. "
    "How should the Guide offer orientation while refusing to replace agency?"
)

EXPECTED_TITLE = "Being in the Driver's Seat (Without Pretending You Control the Road)"
EXPECTED_URL = (
    "https://geralddaquila.com/"
    "being-in-the-drivers-seat-without-pretending-to-control-the-road/"
)


def _send_payload(monkeypatch, payload):
    import main

    # Keep this focused on the shared sender contract, not registry lookup for
    # unrelated exact-query Gold Stars or conceptual doorway families.
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _query: None)
    sent = []

    async def send(message):
        sent.append(message)

    asyncio.run(main._use_send_json(send, payload))
    body = next(item["body"] for item in sent if item["type"] == "http.response.body")
    return json.loads(body.decode("utf-8"))


def test_shared_sender_replaces_provider_answer_with_registered_agency_orientation(monkeypatch):
    import main
    from deterministic_answer_recovery import _guide_personal_decision_agency_recovery

    result = _send_payload(
        monkeypatch,
        {
            "ok": True,
            "query": QUERY,
            "response": "The decision about A user asks for a personal life decision...",
            "provider": "provider-exhaustion-recovery",
        },
    )

    assert result["response"] == _guide_personal_decision_agency_recovery()
    assert "The decision about A user asks" not in result["response"]
    assert result["processing"] == "sender_boundary_personal_decision_agency"
    assert result["recommendation"]["title"] == EXPECTED_TITLE
    assert result["recommendation"]["url"] == EXPECTED_URL
    assert result["canonical_doorway"] == result["recommendation"]


def test_shared_sender_keeps_response_and_answer_aliases_in_sync(monkeypatch):
    from deterministic_answer_recovery import _guide_personal_decision_agency_recovery

    result = _send_payload(
        monkeypatch,
        {
            "ok": True,
            "query": QUERY,
            "response": "Bad provider response.",
            "answer": "Stale answer alias.",
        },
    )

    expected = _guide_personal_decision_agency_recovery()
    assert result["response"] == expected
    assert result["answer"] == expected
    assert result["doorway_title"] == EXPECTED_TITLE
    assert result["doorway_url"] == EXPECTED_URL
    assert result["doorway_rationale"]


def test_shared_sender_does_not_rewrite_unrelated_questions(monkeypatch):
    result = _send_payload(
        monkeypatch,
        {
            "ok": True,
            "query": "What is the difference between authority and power?",
            "response": "An ordinary answer.",
        },
    )

    assert result["response"] == "An ordinary answer."
    assert result.get("processing") != "sender_boundary_personal_decision_agency"
