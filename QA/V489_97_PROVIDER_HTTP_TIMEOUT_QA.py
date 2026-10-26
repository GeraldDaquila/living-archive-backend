"""Regression QA for bounded model HTTP timeout configuration."""
import os
import provider_bank


def main():
    old = os.environ.get("USE_PROVIDER_HTTP_TIMEOUT_SECONDS")
    try:
        os.environ.pop("USE_PROVIDER_HTTP_TIMEOUT_SECONDS", None)
        assert provider_bank._provider_http_timeout() == 8.0
        os.environ["USE_PROVIDER_HTTP_TIMEOUT_SECONDS"] = "6"
        assert provider_bank._provider_http_timeout() == 6.0
        os.environ["USE_PROVIDER_HTTP_TIMEOUT_SECONDS"] = "99"
        assert provider_bank._provider_http_timeout() == 10.0
        os.environ["USE_PROVIDER_HTTP_TIMEOUT_SECONDS"] = "2"
        assert provider_bank._provider_http_timeout() == 5.0
        os.environ["USE_PROVIDER_HTTP_TIMEOUT_SECONDS"] = "invalid"
        assert provider_bank._provider_http_timeout() == 8.0

        # A trickle response must not reset urllib's per-read inactivity timeout.
        # Simulate three small chunks arriving at intervals; the aggregate body
        # exceeds the configured total wall-clock budget and must be rejected.
        from types import SimpleNamespace

        clock = SimpleNamespace(value=0.0)
        original_monotonic = provider_bank.time.monotonic
        original_urlopen = provider_bank.urllib.request.urlopen

        class FakeSocket:
            def __init__(self):
                self.timeouts = []

            def settimeout(self, value):
                self.timeouts.append(value)

        class FakeResponse:
            def __init__(self):
                self.parts = [b'{"a":', b'1', b'}']
                self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=FakeSocket()))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read1(self, size):
                clock.value += 0.4
                return self.parts.pop(0) if self.parts else b""

        fake = FakeResponse()
        provider_bank.time.monotonic = lambda: clock.value
        provider_bank.urllib.request.urlopen = lambda req, timeout: fake
        try:
            try:
                provider_bank._http_json(
                    "https://provider.invalid/chat/completions",
                    {"Authorization": "Bearer test"},
                    {"messages": []},
                    "openrouter",
                    "openrouter/free",
                    timeout=1.0,
                )
            except provider_bank.ProviderCallError as exc:
                assert exc.category == "timeout", exc.category
                assert "total HTTP timeout" in str(exc)
            else:
                raise AssertionError("trickle response exceeded timeout but was accepted")
            assert fake.fp.raw._sock.timeouts
            assert fake.fp.raw._sock.timeouts[-1] <= 1.0
        finally:
            provider_bank.time.monotonic = original_monotonic
            provider_bank.urllib.request.urlopen = original_urlopen

        print("V489.97 BOUNDED PROVIDER HTTP TOTAL WALL-CLOCK TIMEOUT QA: PASS")
    finally:
        if old is None:
            os.environ.pop("USE_PROVIDER_HTTP_TIMEOUT_SECONDS", None)
        else:
            os.environ["USE_PROVIDER_HTTP_TIMEOUT_SECONDS"] = old


if __name__ == "__main__":
    main()
