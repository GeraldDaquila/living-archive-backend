import json

import pytest

import main


def test_request_correlation_id_is_request_local_and_strictly_validated(monkeypatch):
    correlation_id = "0123456789abcdef0123456789abcdef"
    monkeypatch.setattr(
        main._gold_star_ledger,
        "current_request_context",
        lambda: {"request_id": correlation_id},
    )
    assert main._visitor_request_correlation_id() == correlation_id

    monkeypatch.setattr(
        main._gold_star_ledger,
        "current_request_context",
        lambda: {"request_id": "basic-0123456789abcdef"},
    )
    assert main._visitor_request_correlation_id() is None

    monkeypatch.setattr(
        main._gold_star_ledger,
        "current_request_context",
        lambda: None,
    )
    assert main._visitor_request_correlation_id() is None


@pytest.mark.asyncio
async def test_shared_json_sender_stamps_correlation_id_after_response_boundaries(monkeypatch):
    correlation_id = "fedcba9876543210fedcba9876543210"
    monkeypatch.setattr(
        main._gold_star_ledger,
        "current_request_context",
        lambda: {"request_id": correlation_id},
    )
    messages = []

    async def send(message):
        messages.append(message)

    await main._use_send_json(
        send,
        {
            "ok": True,
            "request_id": "basic-0123456789abcdef",
            "query": "",
            "response": "A bounded visitor response.",
        },
        200,
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message.get("type") == "http.response.body"
    )
    payload = json.loads(response_body)
    assert payload["request_id"] == "basic-0123456789abcdef"
    assert payload["request_correlation_id"] == correlation_id
