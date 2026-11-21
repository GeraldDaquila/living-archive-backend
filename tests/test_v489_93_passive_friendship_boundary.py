"""Current contract for lived relationship inquiries on the Guide request boundary.

The lived-relational detector remains useful evidence, but HRN redirect/session
handoff is retired: ordinary relationship questions are answered natively by
The Guide. This suite tests both the detector and that current visitor boundary.
"""
import asyncio
import json
from pathlib import Path

import pytest
import main as use_main

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
TEXT = SOURCE.read_text(encoding="utf-8")

TARGET = "I am struggling with a friendship where I want to be understood but also need boundaries."
NATURAL_TARGET = "I keep putting off a conversation with a friend because I am afraid it will change the friendship."
COMPACT_TARGET = (
    "I keep trying to explain why the same argument hurts me, but we end up "
    "arguing about whether I should still feel hurt."
)


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


def _assert_native_guide_response(status, payload):
    assert status == 200
    assert payload["intent"] == "TOPICAL_INQUIRY"
    assert payload.get("handoff") != "relationship"
    assert payload.get("relational_delegation") is None
    assert isinstance(payload.get("response"), str) and payload["response"].strip()


def test_passive_friendship_detector_preserves_lived_structure():
    decision = use_main._relational_boundary_decision(TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["inquiry"] is True


def test_natural_friend_conversation_detector_preserves_lived_structure():
    decision = use_main._relational_boundary_decision(NATURAL_TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True


def test_compact_repeated_argument_detector_preserves_lived_structure():
    decision = use_main._relational_boundary_decision(COMPACT_TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


@pytest.mark.parametrize("query", [TARGET, NATURAL_TARGET, COMPACT_TARGET])
def test_lived_relationship_questions_are_answered_natively_by_the_guide(query):
    status, payload = asyncio.run(_post_query(query))
    _assert_native_guide_response(status, payload)


def test_identical_openings_do_not_create_legacy_hrn_sessions():
    _, first = asyncio.run(_post_query(TARGET))
    _, second = asyncio.run(_post_query(TARGET))
    assert first.get("handoff") != "relationship"
    assert second.get("handoff") != "relationship"
    assert "relational_delegation" not in first
    assert "relational_delegation" not in second


def test_client_session_token_does_not_revive_retired_hrn_handoff():
    token = "browser-session-token-1234567890"
    status, payload = asyncio.run(_post_query(TARGET, session_id=token))
    _assert_native_guide_response(status, payload)


def test_explanatory_and_archive_queries_do_not_open_lived_relational_boundary():
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


def test_version_integrity_checks_current_release_and_source_identity_contracts():
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
    assert 'if not str(RUNTIME_SOURCE_FINGERPRINT).startswith(f"USE-{APP_VERSION}-source-"):' in TEXT
    assert 'if not str(CANONICAL_BUILD_ID).startswith(f"USE-BUILD-{APP_VERSION}-"):' in TEXT
