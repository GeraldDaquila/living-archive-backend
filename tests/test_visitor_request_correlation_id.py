import json
import re
from pathlib import Path

import pytest

import gold_star_response_floor
import main


@pytest.mark.asyncio
async def test_outermost_visitor_boundary_stamps_the_same_id_as_terminal_telemetry(monkeypatch):
    captured_context = {}
    events = []

    async def fake_request_boundary(scope, receive, send):
        request_context = main._gold_star_ledger.current_request_context()
        captured_context["request_id"] = request_context["request_id"]
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps({
                "ok": True,
                "request_id": "basic-0123456789abcdef",
                "response": "A bounded visitor response.",
            }).encode("utf-8"),
            "more_body": False,
        })

    monkeypatch.setattr(main, "_use_request_boundary", fake_request_boundary)
    monkeypatch.setattr(main, "_guide_finalize_visitor_payload", lambda payload, _query: payload)
    monkeypatch.setattr(main, "_gold_star_attach_route_context", lambda payload, *_args: payload)
    monkeypatch.setattr(main, "_guide_enforce_terminal_doorway_policy", lambda payload, _query: payload)
    monkeypatch.setattr(main, "_guide_sync_power_responsibility_final_metadata", lambda payload: payload)
    monkeypatch.setattr(main, "_guide_reconcile_verified_doorway_recovery", lambda payload: payload)
    monkeypatch.setattr(main, "_final_exact_gold_standard_authority", lambda _query: None)
    monkeypatch.setattr(main.general_guide_composition, "_requires_substantive_answer_contract", lambda _query: False)
    monkeypatch.setattr(
        gold_star_response_floor,
        "apply_response_floor_boundary",
        lambda _query, payload, status, **_kwargs: (payload, status),
    )
    monkeypatch.setattr(
        main,
        "_emit_guide_outcome",
        lambda event, **fields: events.append((event, fields)),
    )

    sent = []

    async def receive():
        return {
            "type": "http.request",
            "body": b'{"query":""}',
            "more_body": False,
        }

    async def send(message):
        sent.append(message)

    await main._guide_outer_visitor_response_boundary(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/query",
            "headers": [(b"content-type", b"application/json")],
        },
        receive,
        send,
    )

    body = b"".join(
        message.get("body", b"")
        for message in sent
        if message.get("type") == "http.response.body"
    )
    payload = json.loads(body)
    correlation_id = payload.get("request_correlation_id")
    assert re.fullmatch(r"[0-9a-f]{32}", correlation_id or "")
    assert correlation_id == captured_context["request_id"]
    assert correlation_id != payload["request_id"]

    terminal = [
        fields for event, fields in events
        if event == "gold_star_request_terminal"
    ]
    assert len(terminal) == 1
    assert terminal[0]["request_id"] == correlation_id


def test_live_smoke_requires_the_unique_correlation_id_not_only_the_stable_query_id():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "live-gold-star-visitor-smoke.yml"
    ).read_text(encoding="utf-8")
    assert 'request_id = str(body.get("request_id") or "")' in workflow
    assert 'request_correlation_id = str(body.get("request_correlation_id") or "")' in workflow
    assert 're.fullmatch(r"[0-9a-f]{32}", request_correlation_id)' in workflow
    assert '"request_correlation_id": request_correlation_id' in workflow
