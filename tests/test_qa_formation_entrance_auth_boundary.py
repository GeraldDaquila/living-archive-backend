"""QA Formation entrance authorization, request-boundary, and log-redaction tests."""
import json

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "qa-formation-secret-test-only")
    monkeypatch.delenv("USE_PROVIDER_BANK_SHARED_SECRET_PREVIOUS", raising=False)
    return TestClient(main.app)


def test_formation_entrance_rejects_missing_auth_before_body_parse(client):
    response = client.post("/api/formation-entrance", content=b"{")

    assert response.status_code == 401
    assert response.json()["detail"] == "Provider Bank gateway authorization failed."


def test_formation_entrance_rejects_wrong_auth(client):
    response = client.post(
        "/api/formation-entrance",
        headers={"X-Living-Archive-Provider-Key": "wrong-secret"},
        json={},
    )

    assert response.status_code == 401


def test_formation_entrance_accepts_auth_then_validates_json(client):
    response = client.post(
        "/api/formation-entrance",
        headers={"X-Living-Archive-Provider-Key": "qa-formation-secret-test-only"},
        content=b"{",
    )

    assert response.status_code == 400
    assert response.json()["error_type"] == "formation_entrance_invalid_json"


def test_formation_entrance_rejects_oversized_body(client):
    response = client.post(
        "/api/formation-entrance",
        headers={"X-Living-Archive-Provider-Key": "qa-formation-secret-test-only"},
        content=b" " * 8193,
    )

    assert response.status_code == 413
    assert response.json()["error_type"] == "formation_entrance_payload_too_large"


def test_formation_entrance_rejects_oversized_fields(client):
    response = client.post(
        "/api/formation-entrance",
        headers={"X-Living-Archive-Provider-Key": "qa-formation-secret-test-only"},
        json={"choice": "x" * 121, "situation": "valid situation", "possibility": "valid possibility"},
    )

    assert response.status_code == 422
    assert response.json()["error_type"] == "formation_entrance_field_too_long"


def test_formation_entrance_redacts_specialist_exception_message(client, monkeypatch, capsys):
    secret = "private-provider-body-sk-live-formation-test"

    def fail_specialist(*args, **kwargs):
        raise RuntimeError("upstream diagnostic " + secret)

    monkeypatch.setattr(main, "invoke_specialist", fail_specialist)
    response = client.post(
        "/api/formation-entrance",
        headers={"X-Living-Archive-Provider-Key": "qa-formation-secret-test-only"},
        json={
            "choice": "Stewardship",
            "situation": "A bounded synthetic QA scenario.",
            "possibility": "A constructive next inquiry.",
        },
    )

    captured = capsys.readouterr()
    assert response.status_code == 503
    assert secret not in captured.out
    assert "exception=RuntimeError" in captured.out
