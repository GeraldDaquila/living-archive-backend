"""Mocked ASGI acceptance tests for the public USE query boundary.

The app/router executes end to end while retrieval and generation are isolated.
No provider credentials, Pinecone calls, or visitor data are used.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

import guide_runtime

client = TestClient(guide_runtime.app)


def _context():
    return {
        "context_blocks": "Title: Synthetic anchor\nURL: https://example.invalid/\nContent: Synthetic evidence.",
        "intent": "TOPICAL_INQUIRY",
        "orientational_frame": {"primary": "general", "scores": {}},
        "canonical_link_context": "Synthetic canonical context",
    }


def test_query_endpoint_returns_public_answer_without_leaking_retrieval_context():
    core = guide_runtime.use_core
    with (
        patch.object(core, "fetch_canonical_context", return_value=_context()) as retrieve,
        patch.object(core, "generate_llm_response", return_value="A grounded synthetic answer.") as generate,
        patch.object(core, "assess_progressive_commitment", return_value={}),
        patch.object(core, "progressive_inquiry_invitation", return_value=""),
        patch.dict("os.environ", {"USE_DEBUG_CONTEXT": "0"}),
    ):
        response = client.post("/api/query", json={"query": "What is stewardship?"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["query"] == "What is stewardship?"
    assert body["response"] == "A grounded synthetic answer."
    assert "canonical_context" not in body
    retrieve.assert_called_once_with("What is stewardship?")
    generate.assert_called_once()


def test_query_endpoint_keeps_empty_input_inside_application_contract():
    response = client.post("/api/query", json={"query": "   "})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["query"] == ""
    assert body["response"] == "Please enter a question to query the archive."


def test_query_endpoint_converts_retrieval_failure_to_readable_json():
    core = guide_runtime.use_core
    with patch.object(core, "fetch_canonical_context", side_effect=TimeoutError("synthetic retrieval timeout")):
        response = client.post("/api/query", json={"query": "Explain governance."})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["query"] == "Explain governance."
    assert body["error_type"] == "application_generation_failure"
    assert "try again" in body["response"].lower()
