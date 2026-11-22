import hashlib
import provider_bank as bank


def test_primary_assignment_is_deterministic_and_near_30_percent(monkeypatch):
    monkeypatch.setenv("USE_SERVER_ROLE", "primary")
    assigned = 0
    for n in range(1000):
        messages=[{"role":"user","content":f"question {n}"}]
        assigned += int(bank._active_active_primary_assignment(messages, "general_guide_composition"))
    assert 240 <= assigned <= 360


def test_secondary_never_recursively_assigns_counterpart(monkeypatch):
    monkeypatch.setenv("USE_SERVER_ROLE", "secondary")
    assert bank._active_active_primary_assignment([{"role":"user","content":"x"}], "general_guide_composition") is False


def test_counterpart_urls_are_role_stable(monkeypatch):
    monkeypatch.delenv("USE_COUNTERPART_PROVIDER_URL", raising=False)
    monkeypatch.setenv("USE_SERVER_ROLE", "primary")
    assert "mirror" in bank._active_active_counterpart_url()
    monkeypatch.setenv("USE_SERVER_ROLE", "secondary")
    assert "living-archive-backend.onrender.com" in bank._active_active_counterpart_url()


def test_active_active_remote_result_is_revalidated(monkeypatch):
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "secret")
    monkeypatch.setenv("USE_SERVER_ROLE", "primary")
    class Response:
        def read(self): return b'{"ok":true,"result":{"answer":"ok"},"provider":"test","model":"m"}'
        def __enter__(self): return self
        def __exit__(self,*args): return False
    monkeypatch.setattr(bank, "urlopen", lambda request, timeout: Response())
    result=bank._active_active_delegate([{"role":"user","content":"q"}], 200, lambda raw: __import__("json").loads(raw), "general_guide_composition", None, None)
    assert result["parsed"]["answer"] == "ok"
    assert result["provider"] == "counterpart:test"


def test_active_active_skips_counterpart_running_a_different_commit(monkeypatch):
    import json

    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "secret")
    monkeypatch.setenv("USE_SERVER_ROLE", "primary")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "primary-commit")
    monkeypatch.setenv(
        "USE_COUNTERPART_PROVIDER_URL",
        "https://mirror.example/api/active-active-guide-capability",
    )
    calls = []

    class Response:
        def read(self):
            return json.dumps({
                "contract": "provider-health-readiness-v1",
                "deployment_commit_sha": "stale-mirror-commit",
            }).encode("utf-8")
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return Response()

    monkeypatch.setattr(bank, "urlopen", fake_urlopen)
    result = bank._active_active_delegate(
        [{"role": "user", "content": "q"}],
        200,
        lambda raw: json.loads(raw),
        "general_guide_composition",
        None,
        None,
    )

    assert result is None
    assert len(calls) == 1
    assert calls[0][0].get_method() == "GET"
    assert calls[0][0].full_url == "https://mirror.example/api/provider-health-readiness"
    assert calls[0][1] == bank.ACTIVE_ACTIVE_READINESS_TIMEOUT_SECONDS


def test_active_active_delegates_only_after_counterpart_commit_matches(monkeypatch):
    import json

    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "secret")
    monkeypatch.setenv("USE_SERVER_ROLE", "primary")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "primary-commit")
    monkeypatch.setenv(
        "USE_COUNTERPART_PROVIDER_URL",
        "https://mirror.example/api/active-active-guide-capability",
    )
    calls = []

    class Response:
        def __init__(self, body):
            self.body = body
        def read(self): return self.body
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_urlopen(request, timeout):
        calls.append(request)
        if request.get_method() == "GET":
            return Response(json.dumps({
                "contract": "provider-health-readiness-v1",
                "deployment_commit_sha": "primary-commit",
            }).encode("utf-8"))
        return Response(
            b'{"ok":true,"result":{"answer":"ok"},"provider":"test","model":"m"}'
        )

    monkeypatch.setattr(bank, "urlopen", fake_urlopen)
    result = bank._active_active_delegate(
        [{"role": "user", "content": "q"}],
        200,
        lambda raw: json.loads(raw),
        "general_guide_composition",
        None,
        None,
    )

    assert result["parsed"]["answer"] == "ok"
    assert [request.get_method() for request in calls] == ["GET", "POST"]
