"""ASGI request-boundary integration for one-sided team-conflict recovery."""
import asyncio
import json

import general_guide_composition
import main as use_main
from one_sided_team_conflict_contract import recover_one_sided_team_conflict_response


QUERY = (
    "A visitor wants to apply an Archive idea to a team conflict but has provided "
    "only one person's account. What context should the Guide ask for before offering a frame?"
)
DECOY = {
    "title": "What Is NESARA and GESARA? Origins, Claims, and Why the Theory Keeps Resurfacing",
    "url": "https://geralddaquila.com/2026/10/19/nesara-gesara-a-vision-for-global-financial-reform-amid-systemic-discontent/",
    "rationale": "Upstream retrieval decoy; must be replaced by the reviewed family doorway.",
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
    start = next(m for m in sent if m["type"] == "http.response.start")
    response_body = b"".join(
        m.get("body", b"") for m in sent if m["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body.decode("utf-8"))


def _install_controlled_runtime(monkeypatch, response):
    context = {
        "intent": "TOPICAL_INQUIRY",
        "authoritative_doorway": DECOY,
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
    monkeypatch.setattr(use_main, "_wordpress_search_canonical_candidates", lambda query, limit=5: [])

    calls = []

    def controlled_provider_bank(**kwargs):
        calls.append(kwargs["operation"])
        candidate = {
            "response": response,
            "recommendation": DECOY,
            "doorway_title": DECOY["title"],
            "doorway_url": DECOY["url"],
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
    return calls


def test_actual_asgi_request_returns_contextual_recovery_and_relevant_doorway(monkeypatch):
    calls = _install_controlled_runtime(
        monkeypatch, recover_one_sided_team_conflict_response()
    )
    status, payload = asyncio.run(_post_query(QUERY))

    assert status == 200
    assert isinstance(payload.get("response"), str)
    response = payload["response"].casefold()
    for required in (
        "one person's account",
        "directly observed",
        "inferred about intent",
        "role and authority",
        "safe and appropriate",
        "retaliation risk",
        "facilitated",
        "understanding, repair",
    ):
        assert required in response, required
    assert payload["recommendation"]["title"] == "Building Trust-Centered Organizations"
    assert payload["recommendation"]["url"] == (
        "https://geralddaquila.com/2026/09/07/building-trust-centered-organizations/"
    )
    assert payload["doorway_selection_status"] == "VERIFIED_RELEVANT_DESTINATION"
    assert payload["doorway_selection_source"] == "reviewed_one_sided_team_conflict_family"
    assert calls == ["general_guide_composition"]


def test_actual_asgi_request_recovers_when_provider_response_omits_required_context(monkeypatch):
    calls = _install_controlled_runtime(
        monkeypatch,
        "There is a disagreement. You should confront the other person and ask what they think.",
    )
    status, payload = asyncio.run(_post_query(QUERY))

    assert status == 200
    response = payload["response"].casefold()
    assert "taking that person's experience seriously" in response
    assert "safe and appropriate" in response
    assert "retaliation risk" in response
    assert "facilitated" in response
    assert payload["recommendation"]["title"] == "Building Trust-Centered Organizations"
    assert payload["recommendation"]["url"] == (
        "https://geralddaquila.com/2026/09/07/building-trust-centered-organizations/"
    )
    assert calls == ["general_guide_composition"]
