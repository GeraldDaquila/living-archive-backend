"""Exercise the candidate Python client against the ephemeral WordPress v2 REST bridge.

The workflow runs each mode in a fresh Python process. This verifies that the
shared WordPress database, rather than process-local cache, carries state
between writer, updater, and reader processes. The local HTTP URL is confined
to this disposable CI environment; production configuration remains HTTPS-only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import provider_health_store


KEY = "groq:000-cross-process-provider-health-v2"


def configure_ephemeral_bridge() -> tuple[str, str]:
    base_url = str(os.environ.get("PROVIDER_HEALTH_WP_BASE_URL") or "").rstrip("/")
    secret = str(os.environ.get("PROVIDER_HEALTH_WP_SECRET") or "")
    if not base_url or not secret:
        raise RuntimeError("Ephemeral WordPress URL and CI-only secret are required.")

    endpoint = base_url + "/?rest_route=/living-archive/v1/provider-health"
    provider_health_store._configuration = lambda: (endpoint, secret)
    return endpoint, secret


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def diagnostic_post(endpoint: str, secret: str, states: dict) -> None:
    """Retry once outside the bounded worker to expose only HTTP status/error code."""
    body = json.dumps(
        {"contract_version": "v2", "states": states},
        separators=(",", ":"),
    ).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Living-Archive-Provider-Key": secret,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            decoded = json.loads(response.read().decode("utf-8"))
            print(
                "DIAGNOSTIC direct WordPress POST: "
                f"http_status={response.status}, "
                f"contract={decoded.get('contract_version')}, "
                f"success={decoded.get('success')}, "
                f"submitted={decoded.get('submitted')}, "
                f"written={decoded.get('written')}"
            )
    except HTTPError as error:
        try:
            decoded = json.loads(error.read().decode("utf-8"))
            error_code = decoded.get("code", "unknown")
        except Exception:
            error_code = "unparseable_error"
        print(f"DIAGNOSTIC direct WordPress POST: http_status={error.code}, error_code={error_code}")


def write(endpoint: str, secret: str) -> None:
    record = {
        "provider": "groq",
        "model": "cross-process-provider-health-v2",
        "operation": "hrn_relational",
        "state": "open",
        "failures": 1,
        "consecutive_failures": 1,
        "cooldown_until": 1500.0,
        "quarantine_until": 0.0,
        "last_error": "synthetic cross-process QA failure",
        "last_success": 900.0,
        "last_failure": 1000.0,
        "category": "timeout",
        "last_operation": "hrn_relational",
        "quality_failures": 0,
        "last_quality_failure": 0.0,
        "last_quality_success": 0.0,
        "quality_cooldown_until": 0.0,
        "quality_error": "",
        "probe_in_flight": True,
    }
    states = {KEY: record}
    saved = provider_health_store.save_remote_states(states)
    if not saved:
        diagnostic_post(endpoint, secret, states)
    require(saved, "Python client did not receive an exact v2 write acknowledgement.")
    print("PASS: Python v2 client wrote shared state through real WordPress REST.")


def update() -> None:
    states = provider_health_store.load_remote_states()
    require(
        isinstance(states, dict) and KEY in states,
        "A fresh process could not read the prior process's state.",
    )
    record = states[KEY]
    require(
        record.get("last_operation") == "hrn_relational",
        "last_operation was lost on the first cross-language round trip.",
    )
    record["last_failure"] = 1001.0
    record["last_operation"] = "general_guide_composition"
    record["consecutive_failures"] = 2
    record["failures"] = 2
    record["cooldown_until"] = 1600.0
    record["last_error"] = "synthetic cross-process QA update"
    require(
        provider_health_store.save_remote_states(states),
        "Python client did not receive an exact v2 update acknowledgement.",
    )
    print("PASS: independent Python process read, updated, and persisted operation-specific state.")


def read() -> None:
    states = provider_health_store.load_remote_states()
    require(
        isinstance(states, dict) and KEY in states,
        "A fresh process could not read the persisted shared state.",
    )
    record = states[KEY]
    require(
        record.get("last_operation") == "general_guide_composition",
        "Updated last_operation did not survive the WordPress round trip.",
    )
    require(
        record.get("last_failure") == 1001.0,
        "Updated failure timestamp did not survive the WordPress round trip.",
    )
    require(
        record.get("cooldown_until") == 1600.0,
        "Updated operation cooldown did not survive the WordPress round trip.",
    )
    require(
        record.get("probe_in_flight") is False,
        "Process-local probe ownership was persisted across processes.",
    )
    print(
        "PASS: third Python process recovered the latest shared state; "
        "last_operation survived and probe ownership reset."
    )


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"write", "update", "read"}:
        raise SystemExit(
            "Usage: python QA/test_provider_health_python_wordpress_integration.py write|update|read"
        )
    endpoint, secret = configure_ephemeral_bridge()
    {"write": lambda: write(endpoint, secret), "update": update, "read": read}[sys.argv[1]]()


if __name__ == "__main__":
    main()
