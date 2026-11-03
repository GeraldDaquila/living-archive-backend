"""Regression tests for provider exception redaction at logs and shared health boundaries."""
import json

import provider_bank


def test_failure_persists_only_safe_summary(monkeypatch):
    state = provider_bank.new_state("groq", "openai/gpt-oss-20b")
    sibling = provider_bank.new_state("groq", "openai/gpt-oss-120b")
    monkeypatch.setattr(provider_bank, "_state", lambda provider, model: state)
    monkeypatch.setitem(
        provider_bank._STATE["models"],
        "groq:openai/gpt-oss-120b",
        sibling,
    )
    recorded = {}

    def capture_record_failure(target, category, error, retry_after=None):
        recorded.update(category=category, error=error, retry_after=retry_after)
        return 30.0

    monkeypatch.setattr(provider_bank, "record_failure", capture_record_failure)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    secret_body = "upstream response contains sk-live-sensitive-value"
    exc = provider_bank.ProviderCallError(
        "Groq HTTP 401: " + secret_body,
        "groq",
        "openai/gpt-oss-20b",
        status_code=401,
        retry_after=17,
        category="http_error",
    )

    provider_bank._failure(exc, "groq", "openai/gpt-oss-20b", operation="general_guide_composition")

    assert recorded["category"] == "authentication"
    assert recorded["retry_after"] == 17
    assert "http_status=401" in recorded["error"]
    assert "retry_after_seconds=17" in recorded["error"]
    assert secret_body not in recorded["error"]
    assert secret_body not in state["last_error"]
    assert secret_body not in sibling["last_error"]
    assert "sk-live-sensitive-value" not in repr(provider_bank.export_health_states({
        "groq:openai/gpt-oss-20b": state,
        "groq:openai/gpt-oss-120b": sibling,
    }))


def test_route_logs_provider_failure_class_not_upstream_body(monkeypatch, capsys):
    candidates = [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "health_state": "healthy",
            "quality_failures": 0,
            "transport_failures": 0,
            "consecutive_failures": 0,
            "last_success": 100.0,
            "capabilities": ["json_object", "long_context", "composition"],
        }
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    monkeypatch.setattr(provider_bank, "_blocked", lambda *args, **kwargs: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda *args, **kwargs: True)
    monkeypatch.setattr(provider_bank, "_failure", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_state", lambda *args, **kwargs: provider_bank.new_state("groq", "openai/gpt-oss-20b"))
    monkeypatch.setattr(provider_bank, "_normalize_operation_result", lambda operation, parsed, messages=None: parsed)

    secret_body = "provider echoed sk-live-sensitive-value in its diagnostic body"

    def fail(*args, **kwargs):
        raise provider_bank.ProviderCallError(
            "Groq HTTP 429: " + secret_body,
            "groq",
            "openai/gpt-oss-20b",
            status_code=429,
            category="http_error",
        )

    monkeypatch.setattr(provider_bank, "_call", fail)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=json.loads,
        operation="general_guide_composition",
    )
    output = capsys.readouterr().out

    assert result is None
    assert "provider=groq" in output
    assert "category=http_error" in output
    assert "http_status=429" in output
    assert secret_body not in output
    assert "sk-live-sensitive-value" not in output
