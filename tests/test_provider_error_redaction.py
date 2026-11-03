"""Regression tests for provider exception redaction at logs and shared health boundaries."""
import json

import provider_bank
import provider_health_store


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
        target["category"] = category
        target["last_error"] = error
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
    assert "category=authentication" in recorded["error"]
    assert "category=authentication" in state["last_error"]
    assert "category=authentication" in sibling["last_error"]
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
    assert "category=provider_failure" in output
    assert "http_status=429" in output
    assert secret_body not in output
    assert "sk-live-sensitive-value" not in output



def test_safe_summary_ignores_malformed_metadata():
    exc = provider_bank.ProviderCallError(
        "synthetic failure with secret body",
        "groq",
        "openai/gpt-oss-20b",
        status_code=object(),
        retry_after=float("inf"),
        category="untrusted_raw_category",
    )

    summary = provider_bank._safe_provider_error_summary(exc, category="authentication")

    assert summary == "exception=ProviderCallError category=authentication"
    assert "secret body" not in summary

def test_quality_rejection_does_not_persist_or_log_visitor_text(monkeypatch, capsys):
    state = {
        "quality_failures": 0,
        "last_quality_failure": 0.0,
        "last_quality_success": 0.0,
        "quality_cooldown_until": 0.0,
        "quality_error": "",
    }
    monkeypatch.setattr(provider_bank, "_quality_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    secret_text = "visitor supplied private detail sk-live-sensitive-value"

    provider_bank._record_quality_rejection(
        "groq", "openai/gpt-oss-20b", "general_guide_composition", secret_text
    )

    output = capsys.readouterr().out
    assert state["quality_error"] == "contract_rejection"
    assert secret_text not in state["quality_error"]
    assert "sk-live-sensitive-value" not in output
    assert "contract_rejection" in output




def test_export_redacts_legacy_shared_health_diagnostics():
    legacy = {
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "last_error": "HTTP 401 upstream body contains sk-live-legacy-secret",
        "quality_error": "visitor supplied private detail sk-live-legacy-secret",
        "last_failure": 100.0,
    }
    exported = provider_health_store.export_health_states({"groq:openai/gpt-oss-20b": legacy})
    serialized = json.dumps(exported)

    assert "sk-live-legacy-secret" not in serialized
    assert exported["groq:openai/gpt-oss-20b"]["last_error"] == (
        "exception=LegacyDiagnostic category=provider_failure"
    )
    assert exported["groq:openai/gpt-oss-20b"]["quality_error"] == "contract_rejection"


def test_merge_redacts_legacy_remote_health_on_empty_local_state():
    local = {}
    remote = {
        "provider": "gemini",
        "model": "gemini-test",
        "last_error": "provider response echoed sk-live-legacy-secret",
        "quality_error": "visitor text sk-live-legacy-secret",
        "last_failure": 200.0,
        "last_success": 100.0,
    }

    merged = provider_health_store.merge_health_state(local, remote, now=250.0)

    assert "sk-live-legacy-secret" not in json.dumps(merged)
    assert merged["last_error"] == "exception=LegacyDiagnostic category=provider_failure"
    assert merged["quality_error"] == "contract_rejection"


def test_merge_redacts_legacy_remote_health_over_existing_local_state():
    local = {
        "provider": "openrouter",
        "model": "model-a",
        "last_error": "local legacy error sk-live-legacy-secret",
        "quality_error": "local visitor text sk-live-legacy-secret",
        "last_failure": 100.0,
        "last_success": 50.0,
        "last_quality_failure": 100.0,
        "last_quality_success": 50.0,
    }
    remote = {
        "provider": "openrouter",
        "model": "model-a",
        "last_error": "remote legacy error sk-live-legacy-secret",
        "quality_error": "remote visitor text sk-live-legacy-secret",
        "last_failure": 200.0,
        "last_success": 150.0,
        "last_quality_failure": 200.0,
        "last_quality_success": 100.0,
    }

    merged = provider_health_store.merge_health_state(local, remote, now=250.0)

    assert "sk-live-legacy-secret" not in json.dumps(merged)
    assert merged["last_error"] == "exception=LegacyDiagnostic category=provider_failure"
    assert merged["quality_error"] == "contract_rejection"



def test_direct_shared_health_write_redacts_legacy_state(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        provider_health_store,
        "_request",
        lambda method, payload, timeout=None: (
            captured.update(method=method, payload=payload) or {"written": 1}
        ),
    )
    legacy = {
        "provider": "nvidia",
        "model": "mistral-large",
        "last_error": "legacy upstream response sk-live-legacy-secret",
        "quality_error": "visitor detail sk-live-legacy-secret",
        "last_failure": 10.0,
    }

    assert provider_health_store.save_remote_states({"nvidia:mistral-large": legacy}) is True
    serialized = json.dumps(captured["payload"])

    assert captured["method"] == "POST"
    assert "sk-live-legacy-secret" not in serialized
    assert captured["payload"]["states"]["nvidia:mistral-large"]["last_error"] == (
        "exception=LegacyDiagnostic category=provider_failure"
    )



def test_remote_shared_health_ingestion_redacts_legacy_state(monkeypatch):
    monkeypatch.setattr(provider_health_store, "_READ_CACHE", None)
    monkeypatch.setattr(provider_health_store, "_READ_CACHE_UNTIL", 0.0)
    monkeypatch.setattr(provider_health_store, "_READ_IN_FLIGHT", None)
    monkeypatch.setattr(provider_health_store, "_READ_IN_FLIGHT_RESULT", None)
    monkeypatch.setattr(
        provider_health_store,
        "_request",
        lambda method, payload=None, timeout=None: {
            "contract_version": provider_health_store.CONTRACT_VERSION,
            "states": {
                "gemini:gemini-test": {
                    "provider": "gemini",
                    "model": "gemini-test",
                    "last_error": "historical provider response sk-live-legacy-secret",
                    "quality_error": "historical visitor text sk-live-legacy-secret",
                }
            },
        },
    )

    loaded = provider_health_store.load_remote_states()

    assert "sk-live-legacy-secret" not in json.dumps(loaded)
    assert loaded["gemini:gemini-test"]["last_error"] == (
        "exception=LegacyDiagnostic category=provider_failure"
    )
    assert loaded["gemini:gemini-test"]["quality_error"] == "contract_rejection"



def test_timeout_failure_is_normalized_before_error_redaction(monkeypatch):
    state = provider_bank.new_state("workers_ai", "@cf/model")
    recorded = {}
    monkeypatch.setattr(provider_bank, "_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)

    def capture_record_failure(target, category, error, retry_after=None):
        recorded.update(category=category, error=error)
        target["category"] = category
        target["last_error"] = error
        target["last_failure"] = 1000.0
        target["cooldown_until"] = 1300.0
        target["quarantine_until"] = 1300.0
        return 300.0

    monkeypatch.setattr(provider_bank, "record_failure", capture_record_failure)
    secret = "private upstream timeout body sk-live-timeout-secret"
    exc = provider_bank.ProviderCallError(
        "request timed out: " + secret,
        "workers_ai",
        "@cf/model",
        category="provider_failure",
    )

    category = provider_bank._failure(exc, "workers_ai", "@cf/model", operation="hrn_relational")

    assert category == "timeout"
    assert recorded["category"] == "timeout"
    assert "category=timeout" in recorded["error"]
    assert secret not in recorded["error"]
    assert secret not in state["last_error"]


def test_timeout_cooldown_cap_uses_structured_category_after_redaction(monkeypatch):
    state = provider_bank.new_state("workers_ai", "@cf/model")
    state.update({
        "category": "timeout",
        "last_error": "exception=TimeoutError category=timeout",
        "last_failure": 1000.0,
        "cooldown_until": 1300.0,
        "quarantine_until": 1300.0,
    })
    monkeypatch.setattr(provider_bank, "blocked", lambda target: True)

    assert provider_bank._blocked(state) is True
    assert state["cooldown_until"] == 1020.0
    assert state["quarantine_until"] == 0.0


def test_timeout_operation_isolation_uses_structured_category_after_redaction(monkeypatch):
    state = provider_bank.new_state("workers_ai", "@cf/model")
    state.update({
        "category": "timeout",
        "last_error": "exception=TimeoutError category=timeout",
        "last_operation": "hrn_relational",
    })
    monkeypatch.setattr(provider_bank, "_blocked", lambda target: True)

    assert provider_bank._blocked_for_operation(state, "general_guide_composition") is False
    assert provider_bank._blocked_for_operation(state, "hrn_relational") is True


def test_legacy_timeout_text_migrates_to_structured_category_before_redaction():
    state = {
        "category": "provider_failure",
        "last_error": "workers_ai read operation timed out with upstream body sk-live-legacy-timeout",
        "quality_error": "",
    }

    sanitized = provider_health_store._sanitize_health_diagnostics(state)

    assert sanitized["category"] == "timeout"
    assert sanitized["last_error"] == "exception=LegacyDiagnostic category=timeout"
    assert "sk-live-legacy-timeout" not in json.dumps(sanitized)


def test_rate_limit_cooldown_is_not_shortened_by_timeout_guard(monkeypatch):
    state = provider_bank.new_state("groq", "model")
    state.update({
        "category": "rate_limited",
        "last_error": "exception=ProviderCallError category=rate_limited",
        "last_failure": 1000.0,
        "cooldown_until": 1300.0,
        "quarantine_until": 1300.0,
    })
    monkeypatch.setattr(provider_bank, "blocked", lambda target: True)

    assert provider_bank._blocked(state) is True
    assert state["cooldown_until"] == 1300.0
    assert state["quarantine_until"] == 1300.0



def test_legacy_local_timeout_state_is_migrated_and_redacted_by_blocker(monkeypatch):
    state = provider_bank.new_state("nvidia", "model")
    state.update({
        "category": "provider_failure",
        "last_error": "provider read operation timed out with body sk-live-local-timeout",
        "last_failure": 1000.0,
        "cooldown_until": 1300.0,
        "quarantine_until": 1300.0,
    })
    monkeypatch.setattr(provider_bank, "blocked", lambda target: True)

    assert provider_bank._blocked(state) is True
    assert state["category"] == "timeout"
    assert state["last_error"] == "exception=LegacyDiagnostic category=timeout"
    assert state["cooldown_until"] == 1020.0
    assert "sk-live-local-timeout" not in json.dumps(state)
