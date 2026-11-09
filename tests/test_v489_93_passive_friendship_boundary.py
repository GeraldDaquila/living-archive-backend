"""Regression contract for native Guide handling after intentional HRN retirement.

The relational classifier remains useful as observational evidence, but the
visitor-facing request path must remain inside The Guide. No HRN specialist
handoff or relational-delegation session may be created.
"""
import asyncio
import json
from pathlib import Path

import main as use_main

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
TEXT = SOURCE.read_text(encoding="utf-8")

TARGET = "I am struggling with a friendship where I want to be understood but also need boundaries."
NATURAL_TARGET = "I keep putting off a conversation with a friend because I am afraid it will change the friendship."
COMPACT_TARGET = (
    "I keep trying to explain why the same argument hurts me, but we end up "
    "arguing about whether I should still feel hurt."
)


async def _post_query(query: str):
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
    start = next(m for m in sent if m["type"] == "http.response.start")
    response_body = b"".join(
        m.get("body", b"") for m in sent if m["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body.decode("utf-8"))


def _assert_native_guide_response(status, payload):
    assert status == 200
    assert payload["intent"] == "TOPICAL_INQUIRY"
    assert payload.get("handoff") != "relationship"
    assert "relational_delegation" not in payload
    assert payload.get("handoff_pending") is not True


def test_passive_friendship_boundary_cues_remain_detectable():
    assert r'\b(?:a|this|our|my)\s+friendship\b' in TEXT
    assert r'\b(?:i|we)\s+(?:want|need|hope|wish)\s+to\s+be\s+(?:understood|heard|seen|respected)\b' in TEXT


def test_exact_passive_friendship_query_is_observed_but_not_delegated():
    decision = use_main._relational_boundary_decision(TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["inquiry"] is True
    status, payload = asyncio.run(_post_query(TARGET))
    _assert_native_guide_response(status, payload)


def test_natural_friend_conversation_remains_native_guide_inquiry():
    decision = use_main._relational_boundary_decision(NATURAL_TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    status, payload = asyncio.run(_post_query(NATURAL_TARGET))
    _assert_native_guide_response(status, payload)


def test_compact_repeated_argument_is_observed_but_not_delegated():
    decision = use_main._relational_boundary_decision(COMPACT_TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True
    status, payload = asyncio.run(_post_query(COMPACT_TARGET))
    _assert_native_guide_response(status, payload)


def test_explanatory_and_archive_queries_do_not_open_relational_observation():
    explanatory = use_main._relational_boundary_decision(
        "What is a relationship and why are relationships important?"
    )
    archive_search = use_main._relational_boundary_decision(
        "Can you find an article in the Living Archive about friendship and boundaries?"
    )
    assert explanatory["open"] is False
    assert archive_search["open"] is False
    assert archive_search["reason"] == "bounded_archive_or_definition_request"


def test_retirement_contract_is_explicit_in_request_boundary():
    assert "The Guide relational inquiry retained natively" in TEXT
    assert "HRN is no longer a visitor-facing destination" in TEXT
    assert "rather than invoking the specialist" in TEXT


def test_bounded_archive_and_definition_exclusions_remain():
    start = TEXT.index("def _relational_boundary_decision(")
    end = TEXT.index("_route_probe_lived_relational =", start)
    body = TEXT[start:end]
    assert "if bounded or definition:" in body
    assert "bounded_archive_or_definition_request" in body


def test_version_integrity_is_sequential():
    version_line = next(
        (line for line in TEXT.splitlines() if line.startswith('APP_VERSION = "')),
        None,
    )
    assert version_line is not None, "APP_VERSION is missing"
    app_version = version_line.split('"')[1]
    assert TEXT.startswith(f"# USE PRODUCTION VERSION: {app_version} — "), "production version header drift"
    assert f'DEPLOYMENT_FINGERPRINT = "USE-{app_version}-' in TEXT
    assert f'CANONICAL_BUILD_ID = "USE-BUILD-{app_version}-' in TEXT
    assert f'if str(APP_VERSION) != "{app_version}":' in TEXT
    assert 'if not str(DEPLOYMENT_FINGERPRINT).startswith(f"USE-{APP_VERSION}-"):' in TEXT
    assert 'if not str(CANONICAL_BUILD_ID).startswith(f"USE-BUILD-{APP_VERSION}-"):' in TEXT
