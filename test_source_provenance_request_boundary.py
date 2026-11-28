"""ASGI request-boundary regression for mixed-source provenance after provider exhaustion."""

import asyncio
import json

import general_guide_composition
import main as use_main
from guide_source_provenance_contract import (
    evaluate_source_provenance_response,
    is_source_provenance_question,
)

QUESTION = (
    "For a sentence that combines a direct quotation, a paraphrase, and an "
    "interpretation, how should the Guide make each layer traceable?"
)

EXPECTED_DOORWAY = {
    "title": "Levels of Claim",
    "url": "https://geralddaquila.com/levels-of-claim/",
}


async def _post_query(query):
    body = json.dumps({"query": query, "history": []}).encode("utf-8")
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


def _install_provider_exhaustion(monkeypatch):
    # Exercise the same provider-exhaustion condition seen in the fourth live
    # attempt, without network calls or dependence on provider availability.
    general_guide_composition._COMPOSITION_CACHE.clear()
    context = {
        "intent": "TOPICAL_INQUIRY",
        "generation_authority_protected_docs": [],
    }
    monkeypatch.setattr(
        use_main.use_core, "fetch_canonical_context", lambda query: dict(context)
    )
    monkeypatch.setattr(use_main._base, "_inquiry_profile", lambda query: {})
    monkeypatch.setattr(use_main, "classify_safety", lambda query, history="": None)
    monkeypatch.setattr(
        use_main, "_basic_inquiry_requires_macro_routing", lambda query: False
    )
    monkeypatch.setattr(
        use_main, "_wordpress_search_canonical_candidates", lambda query, limit=5: []
    )

    calls = []

    def exhausted_provider_bank(**kwargs):
        calls.append(kwargs.get("operation"))
        return None

    monkeypatch.setattr(
        general_guide_composition, "route_with_model_bank", exhausted_provider_bank
    )
    return calls


def test_actual_asgi_request_recovers_the_requested_provenance_method_and_doorway(monkeypatch):
    calls = _install_provider_exhaustion(monkeypatch)
    status, payload = asyncio.run(_post_query(QUESTION))

    assert status == 200
    response = payload["response"]
    assert is_source_provenance_question(QUESTION)
    report = evaluate_source_provenance_response(QUESTION, response)
    assert report["passed"] is True, report["missing"]
    assert "compare realistic options" not in response.casefold()
    assert "people who will live with its consequences" not in response.casefold()
    for required in (
        "smallest practical claim-bearing span",
        "exact wording",
        "precise locator",
        "Guide's own words",
        "scope",
        "Guide's own analysis",
        "reasoning",
        "must not lend",
        "cannot be verified",
    ):
        assert required.casefold() in response.casefold(), required

    recommendation = payload.get("recommendation") or payload.get("canonical_doorway")
    assert recommendation
    assert recommendation["title"] == EXPECTED_DOORWAY["title"]
    assert recommendation["url"] == EXPECTED_DOORWAY["url"]
    assert calls
