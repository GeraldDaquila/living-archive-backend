"""Request-boundary regression for the compound stewardship question.

This exercises the actual ASGI request boundary while stubbing only the
provider/composition result. It proves the real routing boundary does not
turn the compound question into an empty Glossary handoff and preserves the
structured recommendation URL in serialized JSON.
"""
import asyncio
import json

import main as use_main


QUERY = "What is stewardship and why does it matter now more than ever?"
CANONICAL_URL = "https://geralddaquila.com/stewardship-today/"


async def _post_query(query):
    body = json.dumps({"query": query}).encode("utf-8")
    sent = []
    consumed = False

    async def receive():
        nonlocal consumed
        if not consumed:
            consumed = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/query",
        "raw_path": b"/api/query",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 43123),
        "server": ("testserver", 80),
    }
    await use_main._use_request_boundary(scope, receive, send)
    start = next(message for message in sent if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in sent
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body.decode("utf-8"))


def test_compound_stewardship_question_returns_answer_and_separate_recommendation(monkeypatch):
    composition_calls = []

    monkeypatch.setattr(use_main, "classify_safety", lambda query, history="": None)
    monkeypatch.setattr(use_main._base, "_inquiry_profile", lambda query: {})
    monkeypatch.setattr(use_main, "_basic_inquiry_requires_macro_routing", lambda query: False)

    def compose(**kwargs):
        composition_calls.append(kwargs["query"])
        return {
            "ok": True,
            "version": use_main.APP_VERSION,
            "query": kwargs["query"],
            "intent": "TOPICAL_INQUIRY",
            "response": (
                "Stewardship is taking responsibility for something that matters "
                "beyond oneself.\n\nIt matters now because our choices affect "
                "people and systems beyond our immediate reach."
            ),
            "recommendation": {
                "title": "Stewardship Today",
                "url": CANONICAL_URL,
            },
        }

    monkeypatch.setattr(use_main, "_basic_inquiry_response", compose)
    monkeypatch.setattr(
        use_main,
        "_guide_capability_route",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("ordinary explanatory question was reclassified")
        ),
    )

    status, payload = asyncio.run(_post_query(QUERY))

    assert status == 200
    assert payload["intent"] == "TOPICAL_INQUIRY"
    assert "Stewardship is taking responsibility" in payload["response"]
    assert "It matters now because" in payload["response"]
    assert isinstance(payload.get("recommendation"), dict)
    assert payload["recommendation"]["title"] == "Stewardship Today"
    assert payload["recommendation"]["url"] == CANONICAL_URL
    assert payload.get("handoff") != "glossary"
    assert composition_calls == [QUERY]


def test_bounded_stewardship_definition_keeps_native_glossary_handoff():
    status, payload = asyncio.run(_post_query("What is stewardship?"))

    assert status == 200
    assert payload["intent"] == "GLOSSARY_HANDOFF"
    assert payload["handoff"] == "glossary"
    assert payload["glossary_url"] == (
        "https://geralddaquila.com/glossary/?glossary_term=stewardship"
    )
    assert payload["response"] == ""
