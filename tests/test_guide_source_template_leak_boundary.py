"""Regression tests for preventing executable/template fragments in visitor answers."""

import main


def test_source_dump_detector_rejects_leaked_conditional_template():
    leaked = (
        "It sounds like you are carrying a lot. "
        "if (currentTurn === 1) { response = { reflection: '...' }; "
        "else if (currentTurn ===="
    )
    assert main._basic_inquiry_has_source_dump(leaked) is True


def test_source_dump_detector_rejects_next_question_template():
    leaked = 'nextQuestion: "When you look at this friction..."'
    assert main._basic_inquiry_has_source_dump(leaked) is True


def test_source_dump_detector_keeps_ordinary_explanation():
    answer = (
        "A problem can recur when the conditions that produce it remain unchanged. "
        "For example, a team may fix a missed handoff without assigning anyone to confirm receipt."
    )
    assert main._basic_inquiry_has_source_dump(answer) is False


def test_final_boundary_recovers_template_contamination():
    payload = {
        "ok": True,
        "response": (
            "if (currentTurn === 1) { response = { reflection: 'fragmented demands' }; "
            "else if (currentTurn ===="
        ),
        "recommendation": {"title": "Wayfinder"},
    }
    recovered = main._guide_finalize_visitor_payload(
        payload,
        "Why do the same problems keep returning even when everyone involved seems to be trying their best?",
    )
    assert "currentTurn" not in recovered["response"]
    assert "nextQuestion" not in recovered["response"]
    assert recovered["response"] == main._archive_limitation_response()
    assert "outside knowledge" in recovered["response"]
    assert recovered["recommendation"] is None
    assert recovered["answer_basis"]["kind"] == "archive_evidence_unavailable"
    assert recovered["processing"] == "final_visitor_boundary_recovery"


def test_final_boundary_recovers_provider_error_payload():
    payload = {
        "ok": True,
        "intent": "TOPICAL_INQUIRY",
        "response": "Unable to generate a response. GROQ_API_KEY is not configured in backend environment.",
        "recommendation": {"title": "AI vs. Human Stewardship"},
    }
    recovered = main._guide_finalize_visitor_payload(
        payload,
        "I want to learn about AI vs. Human Stewardship: Why Conscious Guidance Matters More Than Ever.",
    )
    assert recovered["response"] == main._archive_limitation_response()
    assert "GROQ_API_KEY" not in recovered["response"]
    assert "Unable to generate a response" not in recovered["response"]
    assert recovered["recommendation"] is None
    assert recovered["answer_basis"]["kind"] == "archive_evidence_unavailable"
    assert recovered["processing"] == "final_visitor_boundary_recovery"


def test_outer_asgi_boundary_catches_leak_from_early_request_exit(monkeypatch):
    import asyncio
    import json

    query = (
        "Why do the same problems keep returning even when everyone involved "
        "seems to be trying their best?"
    )

    async def contaminated_early_exit(scope, receive, send):
        payload = {
            "ok": True,
            "response": (
                'The Archive material: if (currentTurn === 1) { '
                'response = { reflection: "fragmented demands" }; '
                'nextQuestion: "When you look at this friction..."'
            ),
            "recommendation": {"title": "Wayfinder"},
        }
        body = json.dumps(payload).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"application/json; charset=utf-8")],
        })
        await send({"type": "http.response.body", "body": body, "more_body": False})

    monkeypatch.setattr(main, "_use_request_boundary", contaminated_early_exit)
    messages = []

    async def receive():
        return {
            "type": "http.request",
            "body": json.dumps({"query": query}).encode("utf-8"),
            "more_body": False,
        }

    async def send(message):
        messages.append(message)

    asyncio.run(main._guide_outer_visitor_response_boundary(
        {"type": "http", "method": "POST", "path": "/api/query"},
        receive,
        send,
    ))

    response_body = b"".join(
        item.get("body", b"")
        for item in messages
        if item.get("type") == "http.response.body"
    )
    recovered = json.loads(response_body.decode("utf-8"))
    assert "currentTurn" not in recovered["response"]
    assert "nextQuestion" not in recovered["response"]
    assert recovered["response"] == main._archive_limitation_response()
    assert "outside knowledge" in recovered["response"]
    assert recovered["recommendation"] is None
    assert recovered["answer_basis"]["kind"] == "archive_evidence_unavailable"
    assert recovered["processing"] == "final_visitor_boundary_recovery"


def test_outer_asgi_boundary_preserves_clean_json_response(monkeypatch):
    import asyncio
    import json

    payload = {
        "ok": True,
        "response": (
            "A problem can recur when the conditions that produce it remain unchanged."
        ),
        "recommendation": None,
    }

    async def clean_exit(scope, receive, send):
        body = json.dumps(payload).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"application/json; charset=utf-8")],
        })
        await send({"type": "http.response.body", "body": body, "more_body": False})

    monkeypatch.setattr(main, "_use_request_boundary", clean_exit)
    messages = []

    async def receive():
        return {
            "type": "http.request",
            "body": json.dumps({"query": "Why do problems recur?"}).encode("utf-8"),
            "more_body": False,
        }

    async def send(message):
        messages.append(message)

    asyncio.run(main._guide_outer_visitor_response_boundary(
        {"type": "http", "method": "POST", "path": "/api/query"},
        receive,
        send,
    ))

    response_body = b"".join(
        item.get("body", b"")
        for item in messages
        if item.get("type") == "http.response.body"
    )
    assert json.loads(response_body.decode("utf-8")) == payload
