"""Isolated SSE transport boundary for The Guide.

This module does not generate content, route requests, alter HRN, or commit
conversation state. It converts one completed Guide HTTP response into a
server-sent event stream so transport/proxy behavior can be validated before
provider-token streaming is introduced.
"""

from __future__ import annotations

import json
import time
from typing import Any, Awaitable, Callable, Dict, Optional


STREAM_CONTRACT_VERSION = "SSE-VALIDATED-v1"
STREAM_TRANSPORT_VERSION = "0.1.1"
STREAM_PATH = "/api/query-stream"


async def _read_body(receive: Callable[[], Awaitable[Dict[str, Any]]]) -> bytes:
    chunks = []
    while True:
        message = await receive()
        if message.get("type") != "http.request":
            continue
        body = message.get("body", b"") or b""
        if body:
            chunks.append(body)
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def _replay_receive(body: bytes) -> Callable[[], Awaitable[Dict[str, Any]]]:
    sent = False

    async def receive() -> Dict[str, Any]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


async def _send_event(
    send: Callable[[Dict[str, Any]], Awaitable[None]],
    event: str,
    data: Dict[str, Any],
) -> None:
    payload = (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"
    ).encode("utf-8")
    await send({"type": "http.response.body", "body": payload, "more_body": True})


def _chunk_text(text: str, chunk_size: int = 240):
    value = str(text or "")
    for index in range(0, len(value), chunk_size):
        yield value[index:index + chunk_size]


async def validated_query_stream(
    scope: Dict[str, Any],
    receive: Callable[[], Awaitable[Dict[str, Any]]],
    send: Callable[[Dict[str, Any]], Awaitable[None]],
    target_app: Callable[..., Awaitable[None]],
) -> None:
    """Expose a transport-only SSE stream around one completed Guide response.

    The target application remains authoritative. Its response is fully
    generated and returned before any visitor-facing response text is emitted.
    This preserves the HRN voice/safety boundary while proving SSE delivery.
    """

    started = time.perf_counter()
    body = await _read_body(receive)

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"text/event-stream; charset=utf-8"),
                (b"cache-control", b"no-cache, no-store, must-revalidate"),
                (b"connection", b"keep-alive"),
                (b"x-accel-buffering", b"no"),
                (b"x-use-stream-contract", STREAM_CONTRACT_VERSION.encode()),
            ],
        }
    )

    await _send_event(
        send,
        "stream_start",
        {
            "contract": STREAM_CONTRACT_VERSION,
            "state_commit": "deferred",
            "hrn_voice": "protected",
            "validated_output": False,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )

    captured = []

    async def capture_send(message: Dict[str, Any]) -> None:
        captured.append(message)

    try:
        target_scope = dict(scope)
        target_scope["path"] = "/api/query"
        target_scope["raw_path"] = b"/api/query"
        await target_app(target_scope, _replay_receive(body), capture_send)
    except Exception as exc:
        await _send_event(
            send,
            "stream_failed",
            {
                "contract": STREAM_CONTRACT_VERSION,
                "error_type": "target_application_failure",
                "message": str(exc),
                "state_commit": "none",
            },
        )
        await send({"type": "http.response.body", "body": b"", "more_body": False})
        return

    response_status = 200
    response_body = b""
    for message in captured:
        if message.get("type") == "http.response.start":
            response_status = int(message.get("status", 200))
        elif message.get("type") == "http.response.body":
            response_body += message.get("body", b"") or b""

    payload: Optional[Dict[str, Any]] = None
    try:
        decoded = json.loads(response_body.decode("utf-8"))
        if isinstance(decoded, dict):
            payload = decoded
    except Exception:
        payload = None

    if response_status >= 400:
        await _send_event(
            send,
            "stream_failed",
            {
                "contract": STREAM_CONTRACT_VERSION,
                "status": response_status,
                "error_type": (payload or {}).get("error_type", "target_http_error"),
                "state_commit": "none",
            },
        )
        await send({"type": "http.response.body", "body": b"", "more_body": False})
        return

    response_text = str((payload or {}).get("response") or "").strip()
    handoff = str((payload or {}).get("handoff") or "").strip()
    handoff_pending = bool((payload or {}).get("handoff_pending"))

    await _send_event(
        send,
        "response_start",
        {
            "contract": STREAM_CONTRACT_VERSION,
            "validated_output": True,
            "status": response_status,
            "state_commit": "deferred",
        },
    )

    if handoff_pending and handoff:
        await _send_event(
            send,
            "handoff",
            {
                "contract": STREAM_CONTRACT_VERSION,
                "handoff": handoff,
                "state_commit": "deferred",
            },
        )

    for chunk in _chunk_text(response_text):
        await _send_event(
            send,
            "response_text",
            {
                "contract": STREAM_CONTRACT_VERSION,
                "text": chunk,
                "validated_output": True,
                "state_commit": "deferred",
            },
        )

    await _send_event(
        send,
        "response_complete",
        {
            "contract": STREAM_CONTRACT_VERSION,
            "validated_output": True,
            "state_commit": "atomic_after_complete",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    await send({"type": "http.response.body", "body": b"", "more_body": False})


def streaming_entry(
    target_app: Callable[..., Awaitable[None]],
) -> Callable[..., Awaitable[None]]:
    async def app(
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        if (
            scope.get("type") == "http"
            and str(scope.get("method") or "").upper() == "POST"
            and str(scope.get("path") or "") == STREAM_PATH
        ):
            await validated_query_stream(scope, receive, send, target_app)
            return
        await target_app(scope, receive, send)

    return app
