"""Provider Bank gateway shared-secret rotation overlap tests."""
import pytest
from fastapi import HTTPException

import provider_gateway_service as gateway


def test_authorize_accepts_current_secret(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "current-secret-test-only")
    monkeypatch.delenv("USE_PROVIDER_BANK_SHARED_SECRET_PREVIOUS", raising=False)

    gateway.authorize("current-secret-test-only")


def test_authorize_accepts_previous_secret_during_rotation(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "new-secret-test-only")
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET_PREVIOUS", "old-secret-test-only")

    gateway.authorize("old-secret-test-only")
    gateway.authorize("new-secret-test-only")


def test_authorize_rejects_unknown_secret_during_overlap(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "new-secret-test-only")
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET_PREVIOUS", "old-secret-test-only")

    with pytest.raises(HTTPException) as exc:
        gateway.authorize("unrecognized-secret-test-only")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Provider Bank gateway authorization failed."


def test_authorize_requires_current_secret_even_if_previous_is_present(monkeypatch):
    monkeypatch.delenv("USE_PROVIDER_BANK_SHARED_SECRET", raising=False)
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET_PREVIOUS", "old-secret-test-only")

    with pytest.raises(HTTPException) as exc:
        gateway.authorize("old-secret-test-only")

    assert exc.value.status_code == 503


def test_authorize_rejects_empty_or_missing_token(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "current-secret-test-only")
    monkeypatch.delenv("USE_PROVIDER_BANK_SHARED_SECRET_PREVIOUS", raising=False)

    for token in (None, "", "   "):
        with pytest.raises(HTTPException) as exc:
            gateway.authorize(token)
        assert exc.value.status_code == 401
