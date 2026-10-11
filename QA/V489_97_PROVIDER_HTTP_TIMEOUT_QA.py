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
        print("V489.97 BOUNDED PROVIDER HTTP TIMEOUT QA: PASS")
    finally:
        if old is None:
            os.environ.pop("USE_PROVIDER_HTTP_TIMEOUT_SECONDS", None)
        else:
            os.environ["USE_PROVIDER_HTTP_TIMEOUT_SECONDS"] = old


if __name__ == "__main__":
    main()
