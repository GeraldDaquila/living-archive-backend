"""Durable shared provider/model health state over the WordPress database bridge.

This module stores operational health metadata only. It never stores prompts,
visitor content, model outputs, credentials, or specialist policy. When the
bridge is unavailable, callers continue with bounded process-local resilience
and expose that degraded state in diagnostics.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from time import monotonic as _monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONTRACT_VERSION = "v1"
SERVER_CAPACITY_CONTRACT_VERSION = "server-capacity-v1"
DEFAULT_CAPACITY_URL = "https://geralddaquila.com/wp-json/living-archive/v1/server-capacity"
DEFAULT_URL = "https://geralddaquila.com/wp-json/living-archive/v1/provider-health"
# Shared WordPress health state is advisory. Keep network stalls from consuming an inference attempt.
# Local circuit state remains authoritative when the shared bridge is slow or unavailable.
TIMEOUT_SECONDS = 0.25
# The shared health bridge is advisory. Briefly open its local circuit after a
# failed probe so each visitor request does not pay the same network timeout.
CIRCUIT_COOLDOWN_SECONDS = 5.0
_CIRCUIT_LOCK = threading.Lock()
_CIRCUIT_OPEN_UNTIL = 0.0
_CIRCUIT_PROBE_IN_FLIGHT = False
# Shared health is advisory and changes far less frequently than visitor requests.
# A short process-local read cache avoids repeated WordPress reads, while a
# single-flight event prevents concurrent cold-cache requests from stampeding
# the bridge. Cache data is health metadata only and never includes visitor input.
_READ_CACHE_TTL_SECONDS = 2.0
_READ_CACHE_LOCK = threading.Lock()
_READ_CACHE = None
_READ_CACHE_UNTIL = 0.0
_READ_IN_FLIGHT = None
_READ_IN_FLIGHT_RESULT = None
# Cross-service synchronization runs off the visitor request path. The 250ms
# synchronous budget remains the guardrail; background probes may use a longer
# bounded window because they never hold an inference request open.
BACKGROUND_TIMEOUT_SECONDS = 1.5
_BACKGROUND_READ_LOCK = threading.Lock()
_BACKGROUND_READ_THREAD = None
_BACKGROUND_READ_RETRY_AFTER = 0.0
_BACKGROUND_READ_LAST_OK = None
_BACKGROUND_READ_LAST_AT = 0.0
_BACKGROUND_WRITE_LOCK = threading.Lock()
_BACKGROUND_WRITE_THREAD = None
_BACKGROUND_WRITE_PENDING = None
_BACKGROUND_WRITE_RETRY_AFTER = 0.0
_BACKGROUND_WRITE_LAST_OK = None
_BACKGROUND_WRITE_LAST_AT = 0.0
STATE_FIELDS = (
    "provider", "model", "operation", "last_operation", "state", "failures", "consecutive_failures",
    "cooldown_until", "quarantine_until", "last_error", "last_success",
    "last_failure", "category", "credential_fingerprint", "quality_failures", "last_quality_failure",
    "last_quality_success", "quality_cooldown_until", "quality_error",
)

_SAFE_PROVIDER_ERROR_CATEGORIES = {
    "provider_failure", "timeout", "network_failure", "unavailable",
    "invalid_request", "unsupported_request", "authentication",
    "quota_or_billing", "terms_required", "free_tier_daily_quota",
    "rate_limited", "model_unavailable", "structured_output_contract",
    "request_too_large", "invalid_provider_response",
}
_SAFE_QUALITY_DIAGNOSTICS = {"", "contract_rejection", "upstream_movement_brief_input_failure"}


def _sanitize_health_diagnostics(state):
    """Strip legacy upstream/visitor text at every shared-state boundary."""
    if not isinstance(state, dict):
        return state
    raw_error = state.get("last_error")
    if raw_error:
        original = str(raw_error).strip()
        if str(state.get("category") or "") == "provider_failure" and any(
            term in original.casefold() for term in (
                "read operation timed out", "request timed out", "timed out", "timeout",
            )
        ):
            # Migrate legacy prose-derived timeout state before removing the prose.
            state["category"] = "timeout"
        value = original
        safe = (
            len(value) <= 240
            and re.fullmatch(
                r"exception=[A-Za-z_][A-Za-z0-9_]{0,63} category="
                r"(?:provider_failure|timeout|network_failure|unavailable|invalid_request|"
                r"unsupported_request|authentication|quota_or_billing|terms_required|"
                r"free_tier_daily_quota|rate_limited|model_unavailable|"
                r"structured_output_contract|request_too_large|invalid_provider_response)"
                r"(?: http_status=[1-5][0-9]{2})?"
                r"(?: retry_after_seconds=[0-9]+(?:\.[0-9]+)?)?",
                value,
            ) is not None
        )
        category = str(state.get("category") or "provider_failure")
        if category not in _SAFE_PROVIDER_ERROR_CATEGORIES:
            category = "provider_failure"
            state["category"] = category
        state["last_error"] = value if safe else "exception=LegacyDiagnostic category=" + category
    fingerprint = state.get("credential_fingerprint")
    if fingerprint is not None and not re.fullmatch(r"[0-9a-f]{20}", str(fingerprint)):
        state["credential_fingerprint"] = ""
    quality_error = state.get("quality_error")
    if quality_error:
        value = str(quality_error).strip()
        state["quality_error"] = value if value in _SAFE_QUALITY_DIAGNOSTICS else "contract_rejection"
    return state


def _configuration():
    url = str(os.getenv("USE_PROVIDER_HEALTH_STATE_URL") or DEFAULT_URL).strip()
    secret = str(os.getenv("USE_PROVIDER_BANK_SHARED_SECRET") or "").strip()
    if not url.startswith("https://") or not secret:
        return "", ""
    return url, secret



def configuration_status():
    """Expose shared-state configuration readiness without revealing secrets."""
    raw_url = str(os.getenv("USE_PROVIDER_HEALTH_STATE_URL") or "").strip()
    url = raw_url or DEFAULT_URL
    secret_configured = bool(str(os.getenv("USE_PROVIDER_BANK_SHARED_SECRET") or "").strip())
    https_valid = url.startswith("https://")
    return {
        "configured": bool(https_valid and secret_configured),
        "url_configured": bool(raw_url),
        "url_source": "environment" if raw_url else "default",
        "https_valid": https_valid,
        "shared_secret_configured": secret_configured,
    }

def _request(method, payload=None, timeout=None, endpoint_url=None):
    global _CIRCUIT_OPEN_UNTIL, _CIRCUIT_PROBE_IN_FLIGHT
    url, secret = _configuration()
    if endpoint_url:
        url = str(endpoint_url).strip()
    if not url:
        return None

    now = time.monotonic()
    recovery_probe = False
    with _CIRCUIT_LOCK:
        if now < _CIRCUIT_OPEN_UNTIL:
            print(
                "USE provider health store circuit: "
                f"method={method}, state=open, retry_in_seconds={_CIRCUIT_OPEN_UNTIL - now:.1f}"
            )
            return None
        # Only single-flight the half-open recovery probe. Normal healthy-state
        # GET/POST traffic remains concurrent and is not needlessly suppressed.
        if _CIRCUIT_OPEN_UNTIL > 0.0:
            if _CIRCUIT_PROBE_IN_FLIGHT:
                return None
            _CIRCUIT_PROBE_IN_FLIGHT = True
            recovery_probe = True

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store",
        "X-Living-Archive-Provider-Key": secret,
        "User-Agent": "Living-Archive-Provider-Health/1.0",
    }
    request_url = url
    if method == "GET":
        separator = "&" if "?" in request_url else "?"
        request_url += separator + "_la_health_nonce=" + str(time.time_ns())
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = Request(request_url, data=data, headers=headers, method=method)
    request_timeout = TIMEOUT_SECONDS if timeout is None else max(0.05, min(2.0, float(timeout)))
    started = time.monotonic()
    outcome = "error"
    try:
        with urlopen(request, timeout=request_timeout) as response:
            result = json.loads(response.read(512 * 1024 + 1).decode("utf-8", errors="replace"))
        if not isinstance(result, dict) or result.get("contract_version") != CONTRACT_VERSION:
            outcome = "invalid_contract"
            return None
        outcome = "ok"
        return result
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        # Do not log URLs, headers, exception bodies, or credentials.
        return None
    finally:
        elapsed = time.monotonic() - started
        with _CIRCUIT_LOCK:
            if recovery_probe:
                _CIRCUIT_PROBE_IN_FLIGHT = False
            if outcome != "ok":
                _CIRCUIT_OPEN_UNTIL = time.monotonic() + CIRCUIT_COOLDOWN_SECONDS
            elif recovery_probe:
                _CIRCUIT_OPEN_UNTIL = 0.0
        print(
            "USE provider health store timing: "
            f"method={method}, outcome={outcome}, elapsed_seconds={elapsed:.3f}, "
            f"timeout_seconds={request_timeout:.2f}"
        )


def load_remote_states(timeout=None):
    """Return a validated shared snapshot, coalescing concurrent cold reads."""
    global _READ_CACHE, _READ_CACHE_UNTIL, _READ_IN_FLIGHT, _READ_IN_FLIGHT_RESULT
    now = _monotonic()
    with _READ_CACHE_LOCK:
        if _READ_CACHE is not None and now < _READ_CACHE_UNTIL:
            return {key: dict(value) for key, value in _READ_CACHE.items()}
        event = _READ_IN_FLIGHT
        owner = event is None
        if owner:
            event = threading.Event()
            _READ_IN_FLIGHT = event
            _READ_IN_FLIGHT_RESULT = None

    if not owner:
        # The owner gets the only bridge attempt. Waiters may use its result,
        # but never issue a parallel request just because the bridge is slow.
        wait_timeout = TIMEOUT_SECONDS if timeout is None else max(0.05, min(2.0, float(timeout)))
        event.wait(wait_timeout + 0.10)
        with _READ_CACHE_LOCK:
            if _READ_CACHE is not None and _monotonic() < _READ_CACHE_UNTIL:
                return {key: dict(value) for key, value in _READ_CACHE.items()}
            result = _READ_IN_FLIGHT_RESULT
            if isinstance(result, dict):
                return {key: dict(value) for key, value in result.items()}
            return None

    cleaned = None
    try:
        result = _request("GET") if timeout is None else _request("GET", timeout=timeout)
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
            cleaned[key] = _sanitize_health_diagnostics({field: value[field] for field in STATE_FIELDS if field in value})
            cleaned[key]["probe_in_flight"] = False
        return cleaned
    finally:
        with _READ_CACHE_LOCK:
            if cleaned is not None:
                _READ_CACHE = cleaned
                _READ_CACHE_UNTIL = _monotonic() + _READ_CACHE_TTL_SECONDS
                _READ_IN_FLIGHT_RESULT = cleaned
            else:
                _READ_IN_FLIGHT_RESULT = None
            if _READ_IN_FLIGHT is event:
                _READ_IN_FLIGHT = None
            event.set()


def _background_read_worker():
    global _BACKGROUND_READ_THREAD, _BACKGROUND_READ_RETRY_AFTER
    global _BACKGROUND_READ_LAST_OK, _BACKGROUND_READ_LAST_AT
    ok = False
    try:
        ok = isinstance(load_remote_states(timeout=BACKGROUND_TIMEOUT_SECONDS), dict)
    except Exception:
        # Shared health is advisory; an unexpected worker failure must not
        # escape into a visitor request or terminate the application.
        ok = False
    finally:
        with _BACKGROUND_READ_LOCK:
            _BACKGROUND_READ_LAST_OK = ok
            _BACKGROUND_READ_LAST_AT = time.time()
            _BACKGROUND_READ_RETRY_AFTER = 0.0 if ok else _monotonic() + CIRCUIT_COOLDOWN_SECONDS
            _BACKGROUND_READ_THREAD = None


def _start_background_read():
    global _BACKGROUND_READ_THREAD
    with _BACKGROUND_READ_LOCK:
        if _BACKGROUND_READ_THREAD is not None and _BACKGROUND_READ_THREAD.is_alive():
            return False
        if _monotonic() < _BACKGROUND_READ_RETRY_AFTER:
            return False
        thread = threading.Thread(
            target=_background_read_worker,
            name="use-provider-health-read",
            daemon=True,
        )
        _BACKGROUND_READ_THREAD = thread
        thread.start()
        return True


def load_remote_states_nonblocking():
    """Return the latest cached snapshot and schedule refresh without waiting."""
    now = _monotonic()
    with _READ_CACHE_LOCK:
        cached = _READ_CACHE
        fresh = cached is not None and now < _READ_CACHE_UNTIL
        result = {key: dict(value) for key, value in cached.items()} if cached is not None else None
    if not fresh:
        _start_background_read()
    return result


def _background_write_worker():
    global _BACKGROUND_WRITE_THREAD, _BACKGROUND_WRITE_PENDING
    global _BACKGROUND_WRITE_RETRY_AFTER, _BACKGROUND_WRITE_LAST_OK, _BACKGROUND_WRITE_LAST_AT
    try:
        while True:
            with _BACKGROUND_WRITE_LOCK:
                payload = _BACKGROUND_WRITE_PENDING
                _BACKGROUND_WRITE_PENDING = None
            if payload is None:
                break
            ok = save_remote_states(payload, timeout=BACKGROUND_TIMEOUT_SECONDS)
            with _BACKGROUND_WRITE_LOCK:
                _BACKGROUND_WRITE_LAST_OK = bool(ok)
                _BACKGROUND_WRITE_LAST_AT = time.time()
                if not ok:
                    if _BACKGROUND_WRITE_PENDING is None:
                        _BACKGROUND_WRITE_PENDING = payload
                    _BACKGROUND_WRITE_RETRY_AFTER = _monotonic() + CIRCUIT_COOLDOWN_SECONDS
                    break
    except Exception:
        with _BACKGROUND_WRITE_LOCK:
            _BACKGROUND_WRITE_LAST_OK = False
            _BACKGROUND_WRITE_LAST_AT = time.time()
            _BACKGROUND_WRITE_RETRY_AFTER = _monotonic() + CIRCUIT_COOLDOWN_SECONDS
    finally:
        with _BACKGROUND_WRITE_LOCK:
            _BACKGROUND_WRITE_THREAD = None


def _start_background_write():
    global _BACKGROUND_WRITE_THREAD
    with _BACKGROUND_WRITE_LOCK:
        if _BACKGROUND_WRITE_THREAD is not None and _BACKGROUND_WRITE_THREAD.is_alive():
            return False
        thread = threading.Thread(
            target=_background_write_worker,
            name="use-provider-health-write",
            daemon=True,
        )
        _BACKGROUND_WRITE_THREAD = thread
        thread.start()
        return True


def save_remote_states_async(states):
    """Coalesce health snapshots and persist them outside visitor inference."""
    global _BACKGROUND_WRITE_PENDING
    if not isinstance(states, dict) or len(states) > 100:
        return False
    try:
        snapshot = json.loads(json.dumps(states, separators=(",", ":"), ensure_ascii=False))
        for value in snapshot.values():
            if isinstance(value, dict):
                _sanitize_health_diagnostics(value)
    except (TypeError, ValueError):
        return False
    with _BACKGROUND_WRITE_LOCK:
        _BACKGROUND_WRITE_PENDING = snapshot
        if _monotonic() < _BACKGROUND_WRITE_RETRY_AFTER:
            return True
        thread = _BACKGROUND_WRITE_THREAD
        if thread is not None and thread.is_alive():
            return True
    _start_background_write()
    return True


def _background_capacity_worker(snapshot):
    try:
        save_server_capacity(snapshot, timeout=BACKGROUND_TIMEOUT_SECONDS)
    except Exception:
        pass


def publish_server_capacity_async(metrics, role=None, server_id=None):
    """Best-effort publication. Never blocks or retries visitor inference."""
    snapshot = build_server_capacity_snapshot(metrics, role=role, server_id=server_id)
    if not snapshot:
        return False
    thread = threading.Thread(target=_background_capacity_worker, args=(snapshot,), daemon=True, name="server-capacity-publish")
    thread.start()
    return True


def counterpart_server_capacity(role=None, server_id=None, timeout=None):
    """Return the freshest valid counterpart record, or None."""
    role = str(role or os.getenv("USE_SERVER_ROLE") or "").strip().lower()
    server_id = str(server_id or os.getenv("USE_SERVER_ID") or "").strip()
    states = load_server_capacities(timeout=timeout)
    if not isinstance(states, dict):
        return None
    candidates = [v for v in states.values() if v.get("server_id") != server_id and v.get("role") in ("primary","secondary") and v.get("role") != role]
    return max(candidates, key=lambda v: float(v.get("updated_at", 0)), default=None)


def background_status():
    """Expose bounded worker state without leaking data or credentials."""
    with _BACKGROUND_READ_LOCK:
        read_in_flight = _BACKGROUND_READ_THREAD is not None and _BACKGROUND_READ_THREAD.is_alive()
    with _BACKGROUND_WRITE_LOCK:
        write_thread = _BACKGROUND_WRITE_THREAD
        return {
            "read_in_flight": bool(read_in_flight),
            "read_last_ok": _BACKGROUND_READ_LAST_OK,
            "read_last_at": _BACKGROUND_READ_LAST_AT,
            "write_in_flight": bool(write_thread is not None and write_thread.is_alive()),
            "write_pending": _BACKGROUND_WRITE_PENDING is not None,
            "last_write_ok": _BACKGROUND_WRITE_LAST_OK,
            "last_write_at": _BACKGROUND_WRITE_LAST_AT,
        }


def export_health_states(states):
    exported = {}
    for key, value in list(states.items())[:100]:
        if not isinstance(key, str) or not isinstance(value, dict) or len(key) > 191:
            continue
        exported[key] = _sanitize_health_diagnostics({
            field: value.get(field)
            for field in STATE_FIELDS
            if field in value
        })
        exported[key]["probe_in_flight"] = False
    return exported


def save_remote_states(states, timeout=None):
    if not isinstance(states, dict) or len(states) > 100:
        return False
    payload = {"contract_version": CONTRACT_VERSION, "states": export_health_states(states)}
    result = _request("POST", payload) if timeout is None else _request("POST", payload, timeout=timeout)
    return isinstance(result, dict) and isinstance(result.get("written"), int) and result["written"] >= 0


def merge_health_state(local, remote, now=None):
    """Merge events by timestamps; a stale snapshot cannot reopen a newer success."""
    now = time.time() if now is None else float(now)
    if not isinstance(local, dict) or not local:
        local.clear()
        local.update(remote)
        _sanitize_health_diagnostics(local)
        local["probe_in_flight"] = False
        return local
    local_failure = float(local.get("last_failure", 0) or 0)
    remote_failure = float(remote.get("last_failure", 0) or 0)
    local_success = float(local.get("last_success", 0) or 0)
    remote_success = float(remote.get("last_success", 0) or 0)
    latest_failure = max(local_failure, remote_failure)
    latest_success = max(local_success, remote_success)

    if remote_failure > local_failure:
        for field in ("failures", "consecutive_failures", "last_error", "category", "last_operation", "cooldown_until", "quarantine_until"):
            if field in remote:
                local[field] = remote[field]
    elif remote_failure == local_failure and remote_failure > 0:
        local["failures"] = max(int(local.get("failures", 0) or 0), int(remote.get("failures", 0) or 0))
        local["cooldown_until"] = max(float(local.get("cooldown_until", 0) or 0), float(remote.get("cooldown_until", 0) or 0))
        local["quarantine_until"] = max(float(local.get("quarantine_until", 0) or 0), float(remote.get("quarantine_until", 0) or 0))
        if remote.get("last_error"):
            local["last_error"] = remote["last_error"]
            local["category"] = remote.get("category", local.get("category", ""))
        if remote.get("last_operation"):
            local["last_operation"] = remote["last_operation"]
    if remote_success > local_success:
        local["last_success"] = remote_success
    if remote_failure > local_failure:
        local["last_failure"] = remote_failure
    local["last_failure"] = latest_failure
    local["last_success"] = latest_success
    local["probe_in_flight"] = False

    local_quality_failure = float(local.get("last_quality_failure", 0) or 0)
    remote_quality_failure = float(remote.get("last_quality_failure", 0) or 0)
    local_quality_success = float(local.get("last_quality_success", 0) or 0)
    remote_quality_success = float(remote.get("last_quality_success", 0) or 0)
    latest_quality_failure = max(local_quality_failure, remote_quality_failure)
    latest_quality_success = max(local_quality_success, remote_quality_success)
    local["last_quality_failure"] = latest_quality_failure
    local["last_quality_success"] = latest_quality_success
    if remote_quality_failure > local_quality_failure:
        for field in ("quality_failures", "quality_cooldown_until", "quality_error"):
            if field in remote:
                local[field] = remote[field]
    elif remote_quality_failure == local_quality_failure and remote_quality_failure > 0:
        local["quality_failures"] = max(int(local.get("quality_failures", 0) or 0), int(remote.get("quality_failures", 0) or 0))
        local["quality_cooldown_until"] = max(float(local.get("quality_cooldown_until", 0) or 0), float(remote.get("quality_cooldown_until", 0) or 0))
        if remote.get("quality_error"):
            local["quality_error"] = remote["quality_error"]
    if latest_quality_success >= latest_quality_failure:
        local["quality_failures"] = 0
        local["quality_cooldown_until"] = 0.0
        local["quality_error"] = ""

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
    _sanitize_health_diagnostics(local)
    return local


# Server capacity records are deliberately separate from provider health records.
# They contain operational aggregates only—never visitor prompts or responses.
SERVER_CAPACITY_CONTRACT_VERSION = "server-capacity-v1"
SERVER_CAPACITY_TTL_SECONDS = 45.0
SERVER_CAPACITY_FIELDS = ("server_id", "role", "updated_at", "inflight", "viable_provider_score", "recent_llm_success_rate", "recent_exhaustion_rate")



def _capacity_configuration():
    url = str(os.getenv("USE_SERVER_CAPACITY_STATE_URL") or DEFAULT_CAPACITY_URL).strip()
    secret = str(os.getenv("USE_PROVIDER_BANK_SHARED_SECRET") or "").strip()
    if not url.startswith("https://") or not secret:
        return "", ""
    return url, secret


def build_server_capacity_snapshot(metrics, role=None, server_id=None, now=None):
    role = str(role or os.getenv("USE_SERVER_ROLE") or "").strip().lower()
    server_id = str(server_id or os.getenv("USE_SERVER_ID") or "").strip()
    now = time.time() if now is None else float(now)
    state = dict(metrics or {})
    state.update({"role": role, "server_id": server_id, "updated_at": now})
    clean = sanitize_server_capacity(state, now=now)
    if not clean:
        return None
    return {"contract_version": SERVER_CAPACITY_CONTRACT_VERSION, "state": clean}


def save_server_capacity(snapshot, timeout=None):
    url, secret = _capacity_configuration()
    if not url or not secret or not isinstance(snapshot, dict): return False
    state = snapshot.get("state")
    if snapshot.get("contract_version") != SERVER_CAPACITY_CONTRACT_VERSION or not sanitize_server_capacity(state): return False
    result = _request("POST", snapshot, timeout=timeout, endpoint_url=url)
    return isinstance(result, dict) and bool(result.get("written"))


def load_server_capacities(timeout=None):
    url, secret = _capacity_configuration()
    if not url or not secret: return None
    result = _request("GET", timeout=timeout, endpoint_url=url)
    states = result.get("states") if isinstance(result, dict) else None
    if not isinstance(states, dict) or len(states) > 4: return None
    clean = {}
    for key, value in states.items():
        if isinstance(key, str):
            record = sanitize_server_capacity(value)
            if record: clean[key] = record
    return clean

def sanitize_server_capacity(state, now=None):
    """Return a bounded, privacy-safe server-capacity record or None."""
    if not isinstance(state, dict): return None
    now = time.time() if now is None else float(now)
    try:
        updated = float(state.get("updated_at", 0) or 0)
        if updated <= 0 or now - updated > SERVER_CAPACITY_TTL_SECONDS: return None
        role = str(state.get("role") or "").strip().lower(); server_id = str(state.get("server_id") or "").strip()
        if role not in ("primary", "secondary") or not server_id or len(server_id) > 64: return None
        return {"server_id":server_id,"role":role,"updated_at":updated,"inflight":max(0,min(100,int(state.get("inflight",0) or 0))),"viable_provider_score":max(0.0,min(1.0,float(state.get("viable_provider_score",0) or 0))),"recent_llm_success_rate":max(0.0,min(1.0,float(state.get("recent_llm_success_rate",0) or 0))),"recent_exhaustion_rate":max(0.0,min(1.0,float(state.get("recent_exhaustion_rate",0) or 0)))}
    except (TypeError, ValueError): return None

def server_capacity_score(state, now=None):
    """Comparable bounded score; lower load and exhaustion improve viability."""
    clean = sanitize_server_capacity(state, now=now)
    if not clean: return None
    return round(0.45*clean["viable_provider_score"] + 0.35*clean["recent_llm_success_rate"] + 0.15*(1-clean["recent_exhaustion_rate"]) + 0.05*(1-min(1,clean["inflight"]/20)), 4)


SERVER_DELEGATION_MIN_LOCAL_SCORE = 0.55
SERVER_DELEGATION_MIN_ADVANTAGE = 0.15

def choose_server_route(assigned, counterpart, now=None):
    """Return a deterministic advisory route; never delegates on missing or stale state."""
    local_score = server_capacity_score(assigned, now=now)
    remote_score = server_capacity_score(counterpart, now=now)
    if local_score is None:
        return {"route":"assigned","reason":"assigned_state_unknown","assigned_score":None,"counterpart_score":remote_score}
    if remote_score is None:
        return {"route":"assigned","reason":"counterpart_state_unknown","assigned_score":local_score,"counterpart_score":None}
    if local_score >= SERVER_DELEGATION_MIN_LOCAL_SCORE:
        return {"route":"assigned","reason":"assigned_viable","assigned_score":local_score,"counterpart_score":remote_score}
    if remote_score >= local_score + SERVER_DELEGATION_MIN_ADVANTAGE:
        return {"route":"counterpart","reason":"material_quality_advantage","assigned_score":local_score,"counterpart_score":remote_score}
    return {"route":"assigned","reason":"no_material_advantage","assigned_score":local_score,"counterpart_score":remote_score}
