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
