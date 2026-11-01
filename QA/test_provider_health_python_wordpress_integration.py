"""Exercise the candidate Python client against the ephemeral WordPress v2 REST bridge.

The workflow runs each mode in a fresh Python process. This verifies that the
shared WordPress database, rather than process-local cache, carries state
between writer, updater, and reader processes. The local HTTP URL is confined
to this disposable CI environment; production configuration remains HTTPS-only.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

# Running a script from QA/ puts that directory, not the repository root, at
# sys.path[0]. Add the root explicitly so the candidate module is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import provider_health_store


KEY = "groq:cross-process-provider-health-v2"


def configure_ephemeral_bridge() -> None:
    base_url = str(os.environ.get("PROVIDER_HEALTH_WP_BASE_URL") or "").rstrip("/")
    secret = str(os.environ.get("PROVIDER_HEALTH_WP_SECRET") or "")
    if not base_url or not secret:
        raise RuntimeError("Ephemeral WordPress URL and CI-only secret are required.")

    endpoint = base_url + "/?rest_route=/living-archive/v1/provider-health"
    # The ephemeral CI WordPress container serves HTTP on loopback only.
    # Bypass the production HTTPS configuration guard without changing client
    # transport, headers, v2 contract validation, acknowledgement, or deadline.
    provider_health_store._configuration = lambda: (endpoint, secret)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write() -> None:
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
    require(
        provider_health_store.save_remote_states({KEY: record}),
        "Python client did not receive an exact v2 write acknowledgement.",
    )
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
    configure_ephemeral_bridge()
    {"write": write, "update": update, "read": read}[sys.argv[1]]()


if __name__ == "__main__":
    main()
