import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from streaming_transport import validated_query_stream

ROOT = Path(__file__).resolve().parents[1]


def test_sse_completion_preserves_independent_recommendation_envelope():
    source = (ROOT / "streaming_transport.py").read_text(encoding="utf-8")
    assert 'recommendation = (payload or {}).get("recommendation")' in source
    assert '"recommendation": recommendation' in source
    assert '"payload": payload or {}' in source


def _request():
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": b'{"question":"test"}', "more_body": False}

    return receive


def _event_names(messages):
    events = []
    for message in messages:
        body = message.get("body", b"").decode("utf-8", errors="ignore")
        if body.startswith("event: "):
            events.append(body.splitlines()[0][7:])
    return events


def test_stream_executes_target_and_emits_validated_completion():
    async def target(scope, receive, send):
        assert scope["path"] == "/api/query"
        request = await receive()
        assert b'"question":"test"' in request["body"]
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({
            "type": "http.response.body",
            "body": json.dumps({
                "response": "A grounded answer.",
                "recommendation": {"url": "/next"},
                "handoff": "safety",
                "handoff_pending": True,
            }).encode(),
            "more_body": False,
        })

    messages = []

    async def send(message):
        messages.append(message)

    asyncio.run(validated_query_stream(
        {"type": "http", "method": "POST", "path": "/api/query-stream"},
        _request(), send, target,
    ))

    events = _event_names(messages)
    assert events == ["stream_start", "response_start", "handoff", "response_text", "response_complete"]
    complete = next(
        json.loads(m["body"].decode().split("data: ", 1)[1])
        for m in messages
        if m.get("body", b"").startswith(b"event: response_complete")
    )
    assert complete["payload"]["response"] == "A grounded answer."
    assert complete["recommendation"] == {"url": "/next"}
    assert messages[-1]["more_body"] is False


def test_target_application_failure_emits_terminal_failure_without_completion():
    async def target(scope, receive, send):
        raise RuntimeError("synthetic target failure")

    messages = []

    async def send(message):
        messages.append(message)

    asyncio.run(validated_query_stream(
        {"type": "http", "method": "POST", "path": "/api/query-stream"},
        _request(), send, target,
    ))

    events = _event_names(messages)
    assert events == ["stream_start", "stream_failed"]
    assert messages[-1]["more_body"] is False
    failure = next(
        json.loads(m["body"].decode().split("data: ", 1)[1])
        for m in messages
        if m.get("body", b"").startswith(b"event: stream_failed")
    )
    assert failure["error_type"] == "target_application_failure"
    assert failure["state_commit"] == "none"


def test_client_disconnect_during_keepalive_cancels_target_task():
    cancelled = asyncio.Event()

    async def target(scope, receive, send):
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    messages = []

    async def send(message):
        if message.get("body") == b": keep-alive\n\n":
            raise OSError("synthetic client disconnect")
        messages.append(message)

    real_wait_for = asyncio.wait_for

    async def immediate_timeout(awaitable, timeout):
        # Use the real timeout implementation with a short interval. The
        # shield keeps the target task alive until the disconnect cancels it.
        return await real_wait_for(awaitable, timeout=0.001)

    async def run():
        with patch("streaming_transport.asyncio.wait_for", side_effect=immediate_timeout):
            await validated_query_stream(
                {"type": "http", "method": "POST", "path": "/api/query-stream"},
                _request(), send, target,
            )

    with pytest.raises(OSError, match="synthetic client disconnect"):
        asyncio.run(run())

    assert cancelled.is_set(), "target task must not continue after client disconnect"


