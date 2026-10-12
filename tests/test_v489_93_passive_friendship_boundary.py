"""Regression contract for passive friendship routing and isolated HRN sessions in v489.104.

Exercises both the authoritative boundary decision and the real ASGI /api/query
request boundary. Definition-only and explicit Archive-search requests remain bounded.
"""
import asyncio
import json
import re
from pathlib import Path

import main as use_main

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
TEXT = SOURCE.read_text(encoding="utf-8")

TARGET = "I am struggling with a friendship where I want to be understood but also need boundaries."


def _function_body(name: str, next_marker: str) -> str:
    start = TEXT.index(f"def {name}(")
    end = TEXT.index(next_marker, start)
    return TEXT[start:end]


async def _post_query(query: str, session_id: str | None = None):
    body_payload = {"query": query}
    if session_id is not None:
        body_payload["session_id"] = session_id
    body = json.dumps(body_payload).encode("utf-8")
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


def test_passive_friendship_boundary_cues_are_present():
    assert r'\b(?:a|this|our|my)\s+friendship\b' in TEXT
    assert r'\b(?:i|we)\s+(?:want|need|hope|wish)\s+to\s+be\s+(?:understood|heard|seen|respected)\b' in TEXT


def test_exact_passive_friendship_query_opens_hrn_boundary():
    decision = use_main._relational_boundary_decision(TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["inquiry"] is True


def test_real_query_request_boundary_hands_off_to_hrn():
    status, payload = asyncio.run(_post_query(TARGET))
    assert status == 200
    assert payload["intent"] == "RELATIONAL_HANDOFF"
    assert payload["handoff"] == "relationship"
    assert payload["handoff_mode"] == "immediate"
    assert payload["handoff_pending"] is True
    assert payload["relational_delegation"]["specialist_id"] == "relationship"
    assert re.fullmatch(r"relationship-[0-9a-f]{24}", payload["relational_delegation"]["session_id"])


def test_identical_opening_queries_receive_distinct_hrn_sessions():
    _, first = asyncio.run(_post_query(TARGET))
    _, second = asyncio.run(_post_query(TARGET))
    first_id = first["relational_delegation"]["session_id"]
    second_id = second["relational_delegation"]["session_id"]
    assert first_id != second_id, "Identical visitor questions must not share a persisted HRN ledger."


def test_explicit_client_session_token_is_stable_across_retries():
    token = "browser-session-token-1234567890"
    _, first = asyncio.run(_post_query(TARGET, session_id=token))
    _, second = asyncio.run(_post_query(TARGET, session_id=token))
    assert first["relational_delegation"]["session_id"] == second["relational_delegation"]["session_id"]


def test_explanatory_and_archive_queries_do_not_open_hrn_boundary():
    explanatory = use_main._relational_boundary_decision(
        "What is a relationship and why are relationships important?"
    )
    archive_search = use_main._relational_boundary_decision(
        "Can you find an article in the Living Archive about friendship and boundaries?"
    )
    assert explanatory["open"] is False
    assert archive_search["open"] is False
    assert archive_search["reason"] == "bounded_archive_or_definition_request"


def test_bounded_archive_and_definition_exclusions_remain():
    body = _function_body("_relational_boundary_decision", "_route_probe_lived_relational =")
    assert "if bounded or definition:" in body
    assert "bounded_archive_or_definition_request" in body


def test_version_integrity_is_sequential():
    # Track the current release identity contract without pinning the test to a retired release.
    assert 'APP_VERSION = "v489.105"' in TEXT
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v489.105-guide-doorway-recovery-runtime-fix"' in TEXT
    assert 'CANONICAL_BUILD_ID = "USE-BUILD-v489.105-guide-doorway-recovery-runtime-fix"' in TEXT
    assert 'if str(APP_VERSION) != "v489.105":' in TEXT
    assert 'if not str(DEPLOYMENT_FINGERPRINT).startswith(f"USE-{APP_VERSION}-"):' in TEXT
    assert 'if not str(CANONICAL_BUILD_ID).startswith(f"USE-BUILD-{APP_VERSION}-"):' in TEXT
