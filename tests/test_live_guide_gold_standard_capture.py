import io
import json
from email.message import Message
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.qa.capture_live_guide_gold_standard_candidate import (
    CANDIDATE_STATUS,
    capture_one,
    load_candidate,
    validate_endpoint,
)


def _record():
    return {
        "benchmark_id": "candidate-1",
        "status": CANDIDATE_STATUS,
        "query": "How does responsibility differ from carrying everything yourself?",
        "expected_response": None,
        "reconstruction_candidate_response": "Candidate answer; not approved.",
        "original_gold_standard_number": 1,
    }


def test_endpoint_is_limited_to_https_primary_or_mirror():
    assert validate_endpoint("https://living-archive-backend.onrender.com") == "https://living-archive-backend.onrender.com"
    assert validate_endpoint("https://living-archive-backend-mirror.onrender.com/api/query").endswith("/api/query")
    with pytest.raises(ValueError):
        validate_endpoint("http://living-archive-backend.onrender.com")
    with pytest.raises(ValueError):
        validate_endpoint("https://example.com/api/query")
    with pytest.raises(ValueError):
        validate_endpoint("https://living-archive-backend.onrender.com/api/query?x=1")


def test_load_candidate_refuses_to_promote_non_candidate(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"records": [_record()]}), encoding="utf-8")
    assert load_candidate(path, "candidate-1")["status"] == CANDIDATE_STATUS
    registry = {"records": [{**_record(), "status": "FROZEN_REFERENCE_ONLY"}]}
    path.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(ValueError, match="Record status must be"):
        load_candidate(path, "candidate-1")


def test_capture_records_live_response_and_keeps_it_unapproved():
    payload = {
        "ok": True,
        "version": "test-version",
        "request_id": "basic-test",
        "response": "Captured answer.",
        "fingerprint": "fp-test",
    }
    body = json.dumps(payload).encode()
    headers = Message()
    headers["Content-Type"] = "application/json"
    headers["Date"] = "Thu, 23 Oct 2026 00:00:00 GMT"

    class FakeResponse:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *_):
            return False
        def read(self):
            return body
        @property
        def headers(self):
            return headers

    with patch("scripts.qa.capture_live_guide_gold_standard_candidate.urlopen", return_value=FakeResponse()) as mocked:
        result = capture_one(_record(), "https://living-archive-backend.onrender.com/api/query", "abc123")

    mocked.assert_called_once()
    request = mocked.call_args.args[0]
    assert request.method == "POST"
    assert json.loads(request.data.decode())["query"] == _record()["query"]
    assert result["http_status"] == 200
    assert result["response_payload"]["response"] == "Captured answer."
    assert result["application_version"] == "test-version"
    assert result["registry_commit"] == "abc123"
    assert result["historical_exact"] is False
    assert result["user_approved"] is False
    assert result["classification"] == "LIVE_CAPTURE_NOT_YET_REVIEWED"
