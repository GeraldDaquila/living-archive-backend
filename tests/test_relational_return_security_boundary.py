"""Security contract tests for the HRN-to-USE relational return boundary."""

import asyncio

import pytest
from fastapi import HTTPException

import main


class FakeRequest:
    def __init__(self, body=b"", headers=None, stream_error=False):
        self.body = body
        self.headers = headers or {}
        self.stream_error = stream_error
        self.stream_called = False

    async def stream(self):
        self.stream_called = True
        if self.stream_error:
            raise AssertionError("request body must not be read")
        yield self.body


def test_relational_return_rejects_missing_service_credential_before_reading_body(monkeypatch):
    def reject(token):
        assert token is None
        raise HTTPException(status_code=401, detail="authorization failed")

    monkeypatch.setattr(main, "authorize_provider_gateway", reject)
    request = FakeRequest(
        body=b'{"journey_action":"end"}',
        headers={"content-type": "application/json"},
        stream_error=True,
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(main._v48755_relational_return(request))

    assert error.value.status_code == 401
    assert request.stream_called is False


def test_relational_return_rejects_declared_oversize_before_streaming(monkeypatch):
    monkeypatch.setattr(main, "authorize_provider_gateway", lambda _token: None)
    request = FakeRequest(
        headers={
            "X-Living-Archive-Provider-Key": "test-only",
            "content-type": "application/json",
            "content-length": "131073",
        },
        stream_error=True,
    )

    response = asyncio.run(main._v48755_relational_return(request))

    assert response.status_code == 413
    assert request.stream_called is False


def test_relational_return_enforces_streamed_body_limit_without_content_length(monkeypatch):
    monkeypatch.setattr(main, "authorize_provider_gateway", lambda _token: None)
    monkeypatch.setattr(main, "_authorize_relational_return_request", lambda _body, _headers: None)
    request = FakeRequest(
        body=b"x" * 131073,
        headers={
            "X-Living-Archive-Provider-Key": "test-only",
            "content-type": "application/json",
        },
    )

    response = asyncio.run(main._v48755_relational_return(request))

    assert response.status_code == 413


def test_relational_return_rejects_non_json_and_malformed_payloads(monkeypatch):
    monkeypatch.setattr(main, "authorize_provider_gateway", lambda _token: None)
    monkeypatch.setattr(main, "_authorize_relational_return_request", lambda _body, _headers: None)
    non_json = FakeRequest(
        body=b"{}",
        headers={"X-Living-Archive-Provider-Key": "test-only", "content-type": "text/plain"},
    )
    malformed = FakeRequest(
        body=b"{",
        headers={"X-Living-Archive-Provider-Key": "test-only", "content-type": "application/json"},
    )

    assert asyncio.run(main._v48755_relational_return(non_json)).status_code == 415
    assert asyncio.run(main._v48755_relational_return(malformed)).status_code == 400


def test_relational_return_preserves_explicit_closure_contract(monkeypatch):
    monkeypatch.setattr(main, "authorize_provider_gateway", lambda _token: None)
    monkeypatch.setattr(main, "_authorize_relational_return_request", lambda _body, _headers: None)
    request = FakeRequest(
        body=b'{"journey_action":"continue"}',
        headers={
            "X-Living-Archive-Provider-Key": "test-only",
            "content-type": "application/json",
            "content-length": "29",
        },
    )

    response = asyncio.run(main._v48755_relational_return(request))

    assert response.status_code == 409

def test_relational_return_operational_logs_exclude_visitor_content_and_session_id():
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1] / "main.py"
    ).read_text(encoding="utf-8")
    start = source.index("async def _v48755_relational_return(request: Request):")
    end = source.index("# v487.57 — EARLY GUIDE CAPABILITY ROUTING", start)
    handler = source[start:end]

    assert "query={_normalize_query(original_question)" not in handler
    assert "session={session_id or 'none'}" not in handler
    assert "exception_type={type(exc).__name__}" in handler



def _signed_relational_headers(body, secret, timestamp, nonce):
    import hashlib
    import hmac

    signed = timestamp.encode("ascii") + b"\\n" + nonce.encode("ascii") + b"\\n" + body
    signature = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return {
        "x-la-relational-timestamp": timestamp,
        "x-la-relational-nonce": nonce,
        "x-la-relational-signature": signature,
    }


def test_relational_return_hmac_accepts_exact_bounded_body(monkeypatch):
    secret = "test-relational-secret-with-at-least-32-characters"
    body = b'{"journey_action":"end"}'
    monkeypatch.setenv("LA_RELATIONAL_RETURN_SHARED_SECRET", secret)
    headers = _signed_relational_headers(body, secret, "1793610000", "nonce-unique-00000001")
    # Fixed time keeps the test independent of wall-clock drift.
    result = main._authorize_relational_return_request(body, headers, now=1793610000)
    assert result is None


def test_relational_return_hmac_rejects_body_tampering(monkeypatch):
    secret = "test-relational-secret-with-at-least-32-characters"
    body = b'{"journey_action":"end"}'
    monkeypatch.setenv("LA_RELATIONAL_RETURN_SHARED_SECRET", secret)
    headers = _signed_relational_headers(body, secret, "1793610000", "nonce-unique-00000002")
    result = main._authorize_relational_return_request(body + b" ", headers, now=1793610000)
    assert result.status_code == 401


def test_relational_return_hmac_rejects_expired_signature(monkeypatch):
    secret = "test-relational-secret-with-at-least-32-characters"
    body = b'{"journey_action":"end"}'
    monkeypatch.setenv("LA_RELATIONAL_RETURN_SHARED_SECRET", secret)
    headers = _signed_relational_headers(body, secret, "1793610000", "nonce-unique-00000003")
    result = main._authorize_relational_return_request(body, headers, now=1793610400)
    assert result.status_code == 401


def test_relational_return_hmac_rejects_replayed_nonce(monkeypatch):
    secret = "test-relational-secret-with-at-least-32-characters"
    body = b'{"journey_action":"end"}'
    monkeypatch.setenv("LA_RELATIONAL_RETURN_SHARED_SECRET", secret)
    headers = _signed_relational_headers(body, secret, "1793610000", "nonce-unique-00000004")
    assert main._authorize_relational_return_request(body, headers, now=1793610000) is None
    replay = main._authorize_relational_return_request(body, headers, now=1793610000)
    assert replay.status_code == 409
