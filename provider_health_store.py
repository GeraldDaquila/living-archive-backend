"""Durable shared provider/model health state over the WordPress database bridge.

This module stores operational health metadata only. It never stores prompts,
visitor content, model outputs, credentials, or specialist policy. When the
bridge is unavailable, callers continue with bounded process-local resilience
and expose that degraded state in diagnostics.
"""
from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONTRACT_VERSION = "v1"
DEFAULT_URL = "https://geralddaquila.com/wp-json/living-archive/v1/provider-health"
TIMEOUT_SECONDS = 1.2
STATE_FIELDS = (
    "provider", "model", "state", "failures", "consecutive_failures",
    "cooldown_until", "quarantine_until", "last_error", "last_success",
    "last_failure", "category",
)


def _configuration():
    url = str(os.getenv("USE_PROVIDER_HEALTH_STATE_URL") or DEFAULT_URL).strip()
    secret = str(os.getenv("USE_PROVIDER_BANK_SHARED_SECRET") or "").strip()
    if not url.startswith("https://") or not secret:
        return "", ""
    return url, secret


def _request(method, payload=None):
    url, secret = _configuration()
    if not url:
        return None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Living-Archive-Provider-Key": secret,
        "User-Agent": "Living-Archive-Provider-Health/1.0",
    }
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            result = json.loads(response.read(512 * 1024 + 1).decode("utf-8", errors="replace"))
        if not isinstance(result, dict) or result.get("contract_version") != CONTRACT_VERSION:
            return None
        return result
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        # Deliberately omit URL, headers, and exception bodies: they may contain
        # deployment details. The provider bank logs only a generic degradation.
        return None


def load_remote_states():
    result = _request("GET")
    if not isinstance(result, dict):
        return None
    states = result.get("states")
    if not isinstance(states, dict) or len(states) > 100:
        return None
    cleaned = {}
    for key, value in states.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        if len(key) > 191 or ":" not in key:
            continue
        cleaned[key] = {field: value[field] for field in STATE_FIELDS if field in value}
        cleaned[key]["probe_in_flight"] = False
    return cleaned


def export_health_states(states):
    exported = {}
    for key, value in list(states.items())[:100]:
        if not isinstance(key, str) or not isinstance(value, dict) or len(key) > 191:
            continue
        exported[key] = {
            field: value.get(field)
            for field in STATE_FIELDS
            if field in value
        }
        exported[key]["probe_in_flight"] = False
    return exported


def save_remote_states(states):
    if not isinstance(states, dict) or len(states) > 100:
        return False
    result = _request("POST", {"contract_version": CONTRACT_VERSION, "states": states})
    return isinstance(result, dict) and isinstance(result.get("written"), int) and result["written"] >= 0


def merge_health_state(local, remote, now=None):
    """Merge events by timestamps; a stale snapshot cannot reopen a newer success."""
    now = time.time() if now is None else float(now)
    if not isinstance(local, dict) or not local:
        local.clear()
        local.update(remote)
        local["probe_in_flight"] = False
        return local
    local_failure = float(local.get("last_failure", 0) or 0)
    remote_failure = float(remote.get("last_failure", 0) or 0)
    local_success = float(local.get("last_success", 0) or 0)
    remote_success = float(remote.get("last_success", 0) or 0)
    latest_failure = max(local_failure, remote_failure)
    latest_success = max(local_success, remote_success)

    if remote_failure > local_failure:
        for field in ("failures", "consecutive_failures", "last_error", "category", "cooldown_until", "quarantine_until"):
            if field in remote:
                local[field] = remote[field]
    elif remote_failure == local_failure and remote_failure > 0:
        local["failures"] = max(int(local.get("failures", 0) or 0), int(remote.get("failures", 0) or 0))
        local["cooldown_until"] = max(float(local.get("cooldown_until", 0) or 0), float(remote.get("cooldown_until", 0) or 0))
        local["quarantine_until"] = max(float(local.get("quarantine_until", 0) or 0), float(remote.get("quarantine_until", 0) or 0))
        if remote.get("last_error"):
            local["last_error"] = remote["last_error"]
            local["category"] = remote.get("category", local.get("category", ""))
    if remote_success > local_success:
        local["last_success"] = remote_success
    if remote_failure > local_failure:
        local["last_failure"] = remote_failure
    local["last_failure"] = latest_failure
    local["last_success"] = latest_success
    local["probe_in_flight"] = False

    if latest_success >= latest_failure:
        local.update({
            "state": "healthy",
            "consecutive_failures": 0,
            "cooldown_until": 0.0,
            "quarantine_until": 0.0,
            "last_error": "",
            "category": "",
        })
    else:
        local["state"] = "open" if max(
            float(local.get("cooldown_until", 0) or 0),
            float(local.get("quarantine_until", 0) or 0),
        ) > now else "half_open"
    return local
