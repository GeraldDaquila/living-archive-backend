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
    assert recovered["response"].strip()
    assert main._basic_inquiry_has_source_dump(recovered["response"]) is False
    assert recovered["recommendation"] is None
    assert recovered["processing"] == "final_visitor_boundary_recurring_problem_explanation"


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
    assert recovered["response"].strip()
    assert main._basic_inquiry_has_source_dump(recovered["response"]) is False
    assert recovered["recommendation"] is None
    assert recovered["processing"] == "final_visitor_boundary_recurring_problem_explanation"


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
    body = json.loads(response_body.decode("utf-8"))
    assert body["ok"] is True
    # A clean substantive answer receives the independently selected canonical
    # doorway when the Archive has a relevant destination for the inquiry.
    assert body["recommendation"]["title"] == (
        "How Human Systems Spiral: Perception, Action, Feedback, and the Conditions of Human Flourishing"
    )
    assert body["recommendation"]["url"].startswith("https://geralddaquila.com/")
    assert body["recommendation"].get("rationale")
    assert body["doorway_decision"] == "selected"
    # The outer boundary may restore a registered deterministic orientation when a\n    # payload is structurally incomplete; cleanliness means no internal template\n    # metadata leaks into the visitor response, not that the response is immutable.\n    assert body["response"]\n    assert "processing" not in body\n    assert body["route_source"] == "guide_outer_visitor_boundary"

def test_doorway_introduction_strips_concatenated_cms_metadata():
    import general_guide_composition

    source_excerpt = (
        "What precolonial Philippine communities can teach us about governance, "
        "social cohesion, and decision making at the human scale. "
        "Meta Description Long before modern nation states emerged, communities "
        "developed systems of governance rooted in local relationships."
    )
    assert general_guide_composition._sanitize_candidate(source_excerpt) == (
        "What precolonial Philippine communities can teach us about governance, "
        "social cohesion, and decision making at the human scale."
    )


def test_shared_doorway_contract_sanitizes_all_rationale_sources():
    source = {
        "title": "The Barangay Before the State",
        "url": "https://geralddaquila.com/the-barangay-before-the-state/",
        "rationale": (
            "A useful study of human-scale governance. "
            "Meta Description Long before modern nation states emerged..."
        ),
    }
    normalized = main._normalize_authoritative_recommendation(source)
    assert normalized["rationale"] == "A useful study of human-scale governance."
    assert "Meta Description" not in normalized["rationale"]


def test_metadata_only_doorway_rationale_is_omitted_not_exposed():
    source = {
        "title": "A Canonical Resource",
        "url": "https://geralddaquila.com/canonical-resource/",
        "rationale": "Meta Description This is internal search metadata.",
    }
    normalized = main._normalize_authoritative_recommendation(source)
    assert normalized == {
        "title": "A Canonical Resource",
        "url": "https://geralddaquila.com/canonical-resource/",
    }


def test_source_section_excerpt_is_not_published_as_doorway_rationale():
    source = {
        "title": "Being in the Driver’s Seat (Without Pretending You Control the Road)",
        "url": "https://geralddaquila.com/2026/01/20/being-in-the-drivers-seat-without-pretending-you-control-the-road",
        "rationale": (
            "Preface There is a particular moment in prolonged change when something "
            "subtle shifts. The chaos hasn’t fully ended. The losses are still real."
        ),
    }
    normalized = main._normalize_authoritative_recommendation(source)
    assert "rationale" not in normalized
    assert "Preface" not in str(normalized)
    assert "The chaos" not in str(normalized)
