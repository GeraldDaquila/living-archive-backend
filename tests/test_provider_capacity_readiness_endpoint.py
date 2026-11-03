from types import SimpleNamespace

from fastapi import HTTPException

import main


def test_provider_capacity_endpoint_requires_gateway_authorization(monkeypatch):
    called = {"diagnostics": False}

    def deny(_token):
        raise HTTPException(status_code=401, detail="unauthorized")

    def diagnostics(_core):
        called["diagnostics"] = True
        return {}

    monkeypatch.setattr(main, "authorize_provider_gateway", deny)
    monkeypatch.setattr(main, "provider_bank_capacity_diagnostics", diagnostics)

    try:
        main.provider_capacity_readiness(SimpleNamespace(headers={}))
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("capacity diagnostics must require gateway authorization")

    assert called["diagnostics"] is False


def test_provider_capacity_endpoint_returns_non_secret_capacity_snapshot(monkeypatch):
    monkeypatch.setattr(main, "authorize_provider_gateway", lambda _token: None)
    monkeypatch.setattr(main, "provider_bank_capacity_diagnostics", lambda _core: {
        "scope": "instance_local_non_secret_capacity_diagnostics",
        "providers": {"groq": {"credential_configured": True, "credential_fingerprint": "abc123"}},
        "interpretation_limits": ["Different keys may still share an upstream account quota."],
    })

    result = main.provider_capacity_readiness(SimpleNamespace(headers={
        "X-Living-Archive-Provider-Key": "test-gateway-key",
    }))

    assert result["ok"] is True
    assert result["contract"] == "provider-capacity-readiness-v1"
    assert result["capacity"]["providers"]["groq"]["credential_fingerprint"] == "abc123"
    assert "test-gateway-key" not in repr(result)
