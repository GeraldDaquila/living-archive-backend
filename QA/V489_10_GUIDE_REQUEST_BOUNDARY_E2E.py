"""Request-boundary end-to-end contract for the compound stewardship question.

Exercises the actual ASGI request boundary, Basic Inquiry assembly, provider-neutral
composition validation, recommendation authority, and JSON serialization. Only the
external retrieval result and Provider Bank transport are controlled test seams.
"""
import asyncio
import json

import general_guide_composition
import main as use_main


QUERY = "What is stewardship and why does it matter now more than ever?"
CANONICAL_URL = (
    "https://geralddaquila.com/"
    "the-living-archive-navigator-volume-iv-stewardship-exchange/"
)
CANONICAL_TITLE = (
    "The Living Archive Navigator: Volume IV – Stewardship & Exchange"
)
ANSWER = (
    "Stewardship is taking responsibility for something that matters beyond oneself.\n\n"
    "It matters now because our choices affect people and systems beyond our immediate reach.\n\n"
    "It asks us to consider not only what we control, but what we are responsible for "
    "and how our choices affect others."
)


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
    start = next(
        message for message in sent
        if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in sent
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body.decode("utf-8"))


def _install_controlled_provider_and_retrieval(monkeypatch):
    context = {
        "intent": "TOPICAL_INQUIRY",
        "authoritative_doorway": {
            "title": CANONICAL_TITLE,
            "url": CANONICAL_URL,
        },
        "generation_authority_protected_docs": [
            {
                "title": CANONICAL_TITLE,
                "url": CANONICAL_URL,
                "content": (
                    "Stewardship asks what we are responsible for and how "
                    "we care for what affects more than ourselves."
                ),
            }
        ],
    }
    monkeypatch.setattr(
        use_main.use_core, "fetch_canonical_context", lambda query: context
    )
    monkeypatch.setattr(
        use_main._base, "_inquiry_profile", lambda query: {}
    )
    monkeypatch.setattr(
        use_main, "classify_safety", lambda query, history="": None
    )
    monkeypatch.setattr(
        use_main, "_basic_inquiry_requires_macro_routing", lambda query: False
    )

    composition_calls = []

    def controlled_provider_bank(**kwargs):
        composition_calls.append(kwargs["operation"])
        candidate = {
            "response": ANSWER,
            "doorway_title": CANONICAL_TITLE,
            "response_shape": "explanatory",
        }
        parsed = kwargs["parse"](json.dumps(candidate, ensure_ascii=False))
        return {
            "parsed": parsed,
            "provider": "controlled_test_provider",
            "model": "controlled_test_model",
            "preference_order": ["controlled_test_provider:controlled_test_model"],
        }

    monkeypatch.setattr(
        general_guide_composition, "route_with_model_bank", controlled_provider_bank
    )
    return composition_calls


def test_compound_stewardship_question_completes_request_composition_and_recommendation(monkeypatch):
    composition_calls = _install_controlled_provider_and_retrieval(monkeypatch)
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
    assert payload["processing"] == "basic_inquiry"
    assert payload["response"] == ANSWER
    assert len(payload["response"].split("\n\n")) == 3
    assert isinstance(payload.get("recommendation"), dict)
    assert payload["recommendation"] == {
        "title": CANONICAL_TITLE,
        "url": CANONICAL_URL,
    }
    assert payload.get("handoff") != "glossary"
    assert composition_calls == ["general_guide_composition"]


def test_bounded_stewardship_definition_keeps_native_glossary_handoff():
    status, payload = asyncio.run(_post_query("What is stewardship?"))

    assert status == 200
    assert payload["intent"] == "GLOSSARY_HANDOFF"
    assert payload["handoff"] == "glossary"
    assert payload["glossary_url"] == (
        "https://geralddaquila.com/glossary/?glossary_term=stewardship"
    )
    assert payload["response"] == ""
