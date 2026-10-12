"""Contract tests for the public-safe provider health readiness diagnostic."""
import main


def test_provider_health_readiness_reports_degraded_shared_store_without_secrets(monkeypatch):
    monkeypatch.setattr(main, "refresh_shared_health_state", lambda: None)
    monkeypatch.setattr(main, "provider_bank_snapshot", lambda core: {
        "shared_health_configuration": {
            "configured": False,
            "url_configured": False,
            "url_source": "default",
            "https_valid": True,
            "shared_secret_configured": False,
        },
        "shared_health_state": {
            "available": False,
            "mode": "local_fallback",
            "last_error": "do not expose diagnostic detail",
        },
    })

    result = main.provider_health_readiness()

    assert result["ok"] is False
    assert result["contract"] == "provider-health-readiness-v1"
    assert result["shared_health"] == {
        "configured": False,
        "available": False,
        "mode": "local_fallback",
        "url_configured": False,
        "url_source": "default",
        "https_valid": True,
        "shared_secret_configured": False,
    }
    assert "last_error" not in repr(result)
    assert "secret value" not in repr(result)


def test_provider_health_readiness_reports_live_shared_store_only_when_configured_and_available(monkeypatch):
    monkeypatch.setattr(main, "provider_bank_snapshot", lambda core: {
        "shared_health_configuration": {
            "configured": True,
            "url_configured": True,
            "url_source": "environment",
            "https_valid": True,
            "shared_secret_configured": True,
        },
        "shared_health_state": {
            "available": True,
            "mode": "shared",
        },
    })

    result = main.provider_health_readiness()

    assert result["ok"] is True
    assert result["shared_health"]["available"] is True
    assert result["shared_health"]["mode"] == "shared"


def test_provider_health_readiness_fails_closed_on_diagnostic_exception(monkeypatch):
    def fail(_):
        raise RuntimeError("secret should not leak")
    monkeypatch.setattr(main, "refresh_shared_health_state", lambda: None)
    monkeypatch.setattr(main, "provider_bank_snapshot", fail)

    result = main.provider_health_readiness()

    assert result["ok"] is False
    assert result["shared_health"]["mode"] == "diagnostic_failure"
    assert "secret should not leak" not in repr(result)
