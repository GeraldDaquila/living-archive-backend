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
