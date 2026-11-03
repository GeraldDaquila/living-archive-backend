import hashlib
from unittest.mock import patch

import provider_bank


def test_capacity_diagnostics_fingerprint_credentials_without_returning_them():
    secret = "test-groq-api-key-not-for-output"
    cloudflare_token = "test-cloudflare-token"
    cloudflare_account = "test-cloudflare-account"
    environment = {
        "GROQ_API_KEY": secret,
        "CLOUDFLARE_API_TOKEN": cloudflare_token,
        "CLOUDFLARE_ACCOUNT_ID": cloudflare_account,
        "USE_QUOTA_GROQ_TPM": "12000",
    }
    configured = {
        "groq": ["openai/gpt-oss-120b"],
        "workers_ai": ["@cf/google/gemma-4-26b-a4b-it"],
    }
    with patch.dict("os.environ", environment, clear=True), \
         patch.object(provider_bank, "_configured", return_value=configured):
        result = provider_bank.capacity_diagnostics(None)

    groq = result["providers"]["groq"]
    workers = result["providers"]["workers_ai"]
    expected_groq = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:20]
    expected_cloudflare = hashlib.sha256(
        (cloudflare_token + ":" + cloudflare_account).encode("utf-8")
    ).hexdigest()[:20]
    expected_account = hashlib.sha256(cloudflare_account.encode("utf-8")).hexdigest()[:20]

    assert groq["credential_configured"] is True
    assert groq["credential_fingerprint"] == expected_groq
    assert groq["models"] == ["openai/gpt-oss-120b"]
    assert workers["credential_fingerprint"] == expected_cloudflare
    assert result["cloudflare_account_fingerprint"] == expected_account
    assert "cross_instance_atomic_reservations" in result["quota_control"]
    assert result["quota_control"]["cross_instance_atomic_reservations"] is False
    assert secret not in repr(result)
    assert cloudflare_token not in repr(result)
    assert cloudflare_account not in repr(result)
    assert "different keys may still share" in " ".join(result["interpretation_limits"])


def test_capacity_diagnostics_does_not_fabricate_missing_credentials():
    with patch.dict("os.environ", {}, clear=True), \
         patch.object(provider_bank, "_configured", return_value={}):
        result = provider_bank.capacity_diagnostics(None)

    assert result["providers"]["groq"]["credential_configured"] is False
    assert result["providers"]["groq"]["credential_fingerprint"] == ""
    assert result["providers"]["openrouter"]["configured"] is False
    assert result["cloudflare_account_fingerprint"] == ""


def test_capacity_diagnostics_does_not_treat_nvidia_placeholder_as_configured():
    with patch.dict("os.environ", {"NVIDIA_API_KEY": "your_nvidia_api_key"}, clear=True), \
         patch.object(provider_bank, "_configured", return_value={}):
        result = provider_bank.capacity_diagnostics(None)

    assert result["providers"]["nvidia"]["credential_configured"] is False
    assert result["providers"]["nvidia"]["credential_fingerprint"] == ""
