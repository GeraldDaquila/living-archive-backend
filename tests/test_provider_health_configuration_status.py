"""Regression tests for safe shared provider-health configuration diagnostics."""
import provider_health_store


def test_configuration_status_reports_missing_secret_without_exposing_it(monkeypatch):
    monkeypatch.delenv("USE_PROVIDER_HEALTH_STATE_URL", raising=False)
    monkeypatch.delenv("USE_PROVIDER_BANK_SHARED_SECRET", raising=False)

    status = provider_health_store.configuration_status()

    assert status["configured"] is False
    assert status["url_source"] == "default"
    assert status["https_valid"] is True
    assert status["shared_secret_configured"] is False
    assert "value" not in status
    assert "do-not-disclose" not in repr(status)


def test_configuration_status_reports_environment_url_and_secret_presence_only(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_HEALTH_STATE_URL", "https://example.invalid/provider-health")
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "do-not-disclose-this-test-secret")

    status = provider_health_store.configuration_status()

    assert status == {
        "configured": True,
        "url_configured": True,
        "url_source": "environment",
        "https_valid": True,
        "shared_secret_configured": True,
    }
    assert "do-not-disclose-this-test-secret" not in repr(status)


def test_configuration_status_rejects_non_https_endpoint(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_HEALTH_STATE_URL", "http://example.invalid/provider-health")
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "configured")

    status = provider_health_store.configuration_status()

    assert status["configured"] is False
    assert status["https_valid"] is False
    assert status["shared_secret_configured"] is True
