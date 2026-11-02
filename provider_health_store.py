"""Durable shared provider/model health state over the WordPress database bridge.

This module stores operational health metadata only. It never stores prompts,
visitor content, model outputs, credentials, or specialist policy. When the
bridge is unavailable, callers continue with bounded process-local resilience
and expose that degraded state in diagnostics.
"""
from __future__ import annotations

import json
import math
from http.client import HTTPException
import os
import threading
import time
from time import monotonic as _monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONTRACT_VERSION = "v2"
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
# At most one bounded health-bridge transport worker may outlive its caller.
_REQUEST_SLOT = threading.BoundedSemaphore(1)
STATE_FIELDS = (
    "provider", "model", "operation", "state", "failures", "consecutive_failures",
    "cooldown_until", "quarantine_until", "last_error", "last_success",
    "last_failure", "category", "last_operation", "quality_failures", "last_quality_failure",
    "last_quality_success", "quality_cooldown_until", "quality_error",
)


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

def _read_response_body(response, deadline, max_bytes):
    """Read in bounded chunks against one monotonic wall-clock deadline.

    urllib's socket timeout is normally an inactivity timeout. Resetting it to
    the remaining total budget before every read prevents a trickle response
    from extending this advisory health-store call indefinitely.
    """
    read_chunk = getattr(response, "read1", None)
    if not callable(read_chunk):
        raise TimeoutError("total HTTP timeout: incremental response reads unavailable")

    chunks = bytearray()
    while True:
        remaining = deadline - _monotonic()
        if remaining <= 0:
            raise TimeoutError("total HTTP timeout while reading response body")

        response_fp = getattr(response, "fp", None)
        raw = getattr(response_fp, "raw", None)
        sock = getattr(raw, "_sock", None)
        # urllib may expose a buffered response after the underlying socket
        # reference has already been detached (for example, a fully received
        # keep-alive/close response). Consume buffered bytes in that case. The
        # caller's absolute deadline still bounds waiting, and the single worker
        # slot prevents a stalled detached reader from creating a worker backlog.
        if sock is not None:
            sock.settimeout(remaining)

        chunk = read_chunk(min(65536, max_bytes + 1 - len(chunks)))
        if not chunk:
            break
        chunks.extend(chunk)
        if len(chunks) > max_bytes:
            raise ValueError("provider health response exceeds maximum size")
        if _monotonic() >= deadline:
            raise TimeoutError("total HTTP timeout while reading response body")

    if _monotonic() > deadline:
        raise TimeoutError("total HTTP timeout after response body")
    return bytes(chunks)


def _request(method, payload=None, on_late_result=None):
    """Bound caller wait across DNS, TLS, headers, and response-body transport.

    urllib socket timeouts cannot bound every blocking phase. A daemon worker
    performs the blocking I/O while the caller waits only for the total budget.
    One process-wide slot prevents timed-out workers from accumulating.
    """
    global _CIRCUIT_OPEN_UNTIL, _CIRCUIT_PROBE_IN_FLIGHT
    url, secret = _configuration()
    if not url:
        return None

    # Build and serialize the request before reserving the sole transport slot.
    # A malformed URL or unexpected non-JSON-safe health value must not strand
    # the process-wide worker semaphore and disable all later bridge attempts.
    try:
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
    except (TypeError, ValueError, UnicodeError, OSError) as error:
        print(f"USE provider health store request preparation failed: method={method}, error_type={type(error).__name__}")
        return None

    now = _monotonic()
    recovery_probe = False
    with _CIRCUIT_LOCK:
        if now < _CIRCUIT_OPEN_UNTIL:
            print(
                "USE provider health store circuit: "
                f"method={method}, state=open, retry_in_seconds={_CIRCUIT_OPEN_UNTIL - now:.1f}"
            )
            return None
        if _CIRCUIT_OPEN_UNTIL > 0.0:
            if _CIRCUIT_PROBE_IN_FLIGHT:
                return None
            _CIRCUIT_PROBE_IN_FLIGHT = True
            recovery_probe = True

    started = _monotonic()
    deadline = started + TIMEOUT_SECONDS
    if not _REQUEST_SLOT.acquire(blocking=False):
        with _CIRCUIT_LOCK:
            if recovery_probe:
                _CIRCUIT_PROBE_IN_FLIGHT = False
            _CIRCUIT_OPEN_UNTIL = _monotonic() + CIRCUIT_COOLDOWN_SECONDS
        print(
            "USE provider health store timing: "
            f"method={method}, outcome=worker_busy, elapsed_seconds={_monotonic() - started:.3f}, "
            f"timeout_seconds={TIMEOUT_SECONDS:.2f}"
        )
        return None

    completed = threading.Event()
    completion_lock = threading.Lock()
    result_box = {
        "outcome": "error",
        "result": None,
        "completed_at": None,
        "caller_decided": False,
        "caller_accepted": False,
        "callback_dispatched": False,
    }

    def dispatch_late_result_if_needed():
        # The caller and worker may both observe completion. Claim the callback
        # under one lock so a late acknowledgement is consumed exactly once.
        callback_result = None
        with completion_lock:
            if (
                completed.is_set()
                and result_box["caller_decided"]
                and not result_box["caller_accepted"]
                and not result_box["callback_dispatched"]
                and result_box["outcome"] == "ok"
                and callable(on_late_result)
            ):
                result_box["callback_dispatched"] = True
                callback_result = result_box["result"]
        if callback_result is not None:
            try:
                on_late_result(callback_result)
            except Exception as callback_error:
                print(
                    "USE provider health store late-ack callback failed: "
                    f"error_type={type(callback_error).__name__}"
                )

    def transport_worker():
        try:
            remaining = deadline - _monotonic()
            if remaining <= 0:
                raise TimeoutError("total HTTP timeout before request")
            with urlopen(request, timeout=remaining) as response:
                body = _read_response_body(response, deadline, 512 * 1024)
                result = json.loads(body.decode("utf-8", errors="replace"))
            with completion_lock:
                if isinstance(result, dict) and result.get("contract_version") == CONTRACT_VERSION:
                    result_box["outcome"] = "ok"
                    result_box["result"] = result
                else:
                    result_box["outcome"] = "invalid_contract"
        except HTTPError as error:
            # HTTP status is safe operational metadata; never log response bodies,
            # URLs, request headers, or credentials.
            with completion_lock:
                result_box["outcome"] = f"http_error_{int(error.code)}"
        except (URLError, HTTPException, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
            with completion_lock:
                result_box["outcome"] = "transport_error_" + type(error).__name__
                if isinstance(error, TimeoutError):
                    # These are fixed internal guard messages, not request or provider data.
                    result_box["error_reason"] = str(error)[:100]
        except Exception as error:
            with completion_lock:
                result_box["outcome"] = "unexpected_error_" + type(error).__name__
        finally:
            # Publish the result and completion timestamp atomically. The caller
            # can accept a pre-deadline result even if it is rescheduled before
            # Event.set(); this closes the narrow lost-ack race at the deadline.
            with completion_lock:
                result_box["completed_at"] = _monotonic()
            _REQUEST_SLOT.release()
            completed.set()
            dispatch_late_result_if_needed()

    worker = threading.Thread(
        target=transport_worker,
        name="provider-health-bridge",
        daemon=True,
    )
    try:
        worker.start()
    except RuntimeError:
        _REQUEST_SLOT.release()
        with completion_lock:
            result_box["outcome"] = "worker_start_failed"
            result_box["completed_at"] = _monotonic()
            result_box["caller_decided"] = True
        completed.set()

    completed.wait(max(0.0, deadline - _monotonic()))
    # Completion time, not Event scheduling, decides whether the response met
    # the caller deadline. If the caller already timed out, a valid response
    # is routed through the one-shot late-ack callback after the slot is free.
    with completion_lock:
        completed_at = result_box.get("completed_at")
        if completed_at is not None and completed_at <= deadline:
            outcome = result_box["outcome"]
            result = result_box["result"]
            result_box["caller_accepted"] = outcome == "ok"
            result_box["caller_decided"] = True
        else:
            outcome = "total_deadline_exceeded"
            result = None
            result_box["caller_decided"] = True
    dispatch_late_result_if_needed()

    elapsed = _monotonic() - started
    with _CIRCUIT_LOCK:
        if recovery_probe:
            _CIRCUIT_PROBE_IN_FLIGHT = False
        if outcome != "ok":
            _CIRCUIT_OPEN_UNTIL = _monotonic() + CIRCUIT_COOLDOWN_SECONDS
        elif recovery_probe:
            _CIRCUIT_OPEN_UNTIL = 0.0
    reason = result_box.get("error_reason", "")
    print(
        "USE provider health store timing: "
        f"method={method}, outcome={outcome}, elapsed_seconds={elapsed:.3f}, "
        f"timeout_seconds={TIMEOUT_SECONDS:.2f}"
        + (f", reason={reason}" if reason else "")
    )
    return result


def _clean_remote_health_payload(result):
    if not isinstance(result, dict) or result.get("contract_version") != CONTRACT_VERSION:
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


def _fetch_validated_remote_states(event=None):
    def accept_late_result(result):
        cleaned_late = _clean_remote_health_payload(result)
        if cleaned_late is None:
            return
        # A late GET is useful for the next route, even though it cannot extend
        # the current visitor's wait. Never let an older read overwrite a newer
        # refresh that has already taken ownership of the single-flight slot.
        with _READ_CACHE_LOCK:
            if _READ_IN_FLIGHT is None or _READ_IN_FLIGHT is event:
                global _READ_CACHE, _READ_CACHE_UNTIL
                _READ_CACHE = cleaned_late
                _READ_CACHE_UNTIL = _monotonic() + _READ_CACHE_TTL_SECONDS

    result = _request("GET", on_late_result=accept_late_result)
    return _clean_remote_health_payload(result)


def _publish_remote_read(event, cleaned):
    global _READ_CACHE, _READ_CACHE_UNTIL, _READ_IN_FLIGHT, _READ_IN_FLIGHT_RESULT
    with _READ_CACHE_LOCK:
        if cleaned is not None:
            _READ_CACHE = cleaned
            _READ_CACHE_UNTIL = _monotonic() + _READ_CACHE_TTL_SECONDS
        elif _READ_CACHE is not None:
            # Retain the last known-good health snapshot and briefly back off
            # another refresh attempt instead of stampeding a slow bridge.
            _READ_CACHE_UNTIL = _monotonic() + 1.0
        _READ_IN_FLIGHT_RESULT = cleaned
        if _READ_IN_FLIGHT is event:
            _READ_IN_FLIGHT = None
        event.set()


def _refresh_remote_states_background(event):
    cleaned = None
    try:
        cleaned = _fetch_validated_remote_states(event)
    except Exception as error:
        print(
            "USE provider health store background refresh failed: "
            f"error_type={type(error).__name__}"
        )
    finally:
        _publish_remote_read(event, cleaned)


def load_remote_states():
    """Return cached shared health immediately; refresh expired snapshots off-path."""
    global _READ_IN_FLIGHT, _READ_IN_FLIGHT_RESULT
    now = _monotonic()
    with _READ_CACHE_LOCK:
        cached = (
            {key: dict(value) for key, value in _READ_CACHE.items()}
            if isinstance(_READ_CACHE, dict)
            else None
        )
        if cached is not None and now < _READ_CACHE_UNTIL:
            return cached
        event = _READ_IN_FLIGHT
        owner = event is None
        if owner:
            event = threading.Event()
            _READ_IN_FLIGHT = event
            _READ_IN_FLIGHT_RESULT = None

    if cached is not None:
        # Stale-while-revalidate: do not make a visitor wait for an expired
        # advisory snapshot. A single background owner refreshes the shared
        # WordPress state; this request continues with its last known-good copy.
        if owner:
            worker = threading.Thread(
                target=_refresh_remote_states_background,
                args=(event,),
                name="provider-health-read-refresh",
                daemon=True,
            )
            try:
                worker.start()
            except RuntimeError:
                _publish_remote_read(event, None)
        return cached

    if not owner:
        # On a cold process start there is no stale snapshot to serve. Preserve
        # the existing bounded single-flight wait so one caller can establish
        # the first shared baseline while concurrent callers never stampede.
        event.wait(TIMEOUT_SECONDS)
        with _READ_CACHE_LOCK:
            if _READ_CACHE is not None and _monotonic() < _READ_CACHE_UNTIL:
                return {key: dict(value) for key, value in _READ_CACHE.items()}
            result = _READ_IN_FLIGHT_RESULT
            if isinstance(result, dict):
                return {key: dict(value) for key, value in result.items()}
            return None

    cleaned = None
    try:
        cleaned = _fetch_validated_remote_states()
        return cleaned
    finally:
        _publish_remote_read(event, cleaned)


def _state_recency(value):
    """Rank bounded exports by their newest transport or quality event."""
    timestamps = []
    for field in ("last_success", "last_failure", "last_quality_success", "last_quality_failure"):
        try:
            timestamp = float(value.get(field, 0) or 0)
        except (TypeError, ValueError):
            timestamp = 0.0
        if not math.isfinite(timestamp) or timestamp < 0:
            timestamp = 0.0
        timestamps.append(timestamp)
    return max(timestamps, default=0.0)


def export_health_states(states):
    """Export the 100 most recently active records with deterministic key ties."""
    eligible = [
        (key, value)
        for key, value in states.items()
        if isinstance(key, str) and 0 < len(key) <= 191 and isinstance(value, dict)
    ]
    eligible.sort(key=lambda item: (-_state_recency(item[1]), item[0]))
    exported = {}
    for key, value in eligible[:100]:
        exported[key] = {
            field: value.get(field)
            for field in STATE_FIELDS
            if field in value
        }
        exported[key]["probe_in_flight"] = False
    return exported


def _is_exact_write_acknowledgement(result, submitted):
    """Validate the complete v2 commit acknowledgement without coercion."""
    if not isinstance(result, dict):
        return False
    if result.get("contract_version") != CONTRACT_VERSION or result.get("success") is not True:
        return False
    acknowledged_submitted = result.get("submitted")
    written = result.get("written")
    # bool is a subclass of int in Python; reject it explicitly.
    if isinstance(acknowledged_submitted, bool) or not isinstance(acknowledged_submitted, int):
        return False
    if isinstance(written, bool) or not isinstance(written, int):
        return False
    return acknowledged_submitted == submitted and written == submitted


def save_remote_states(states, on_late_success=None):
    """Accept an exact v2 acknowledgement, including a validated late commit."""
    if not isinstance(states, dict) or len(states) > 100:
        return False
    submitted = len(states)

    def handle_late_result(result):
        if _is_exact_write_acknowledgement(result, submitted) and callable(on_late_success):
            on_late_success()

    payload = {"contract_version": CONTRACT_VERSION, "states": states}
    if callable(on_late_success):
        result = _request("POST", payload, on_late_result=handle_late_result)
    else:
        result = _request("POST", payload)
    return _is_exact_write_acknowledgement(result, submitted)


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
        for field in ("failures", "consecutive_failures", "last_error", "category", "cooldown_until", "quarantine_until", "last_operation"):
            if field in remote:
                local[field] = remote[field]
    elif remote_failure == local_failure and remote_failure > 0:
        local["failures"] = max(int(local.get("failures", 0) or 0), int(remote.get("failures", 0) or 0))
        local_consecutive = int(local.get("consecutive_failures", 0) or 0)
        remote_consecutive = int(remote.get("consecutive_failures", 0) or 0)
        local["consecutive_failures"] = max(local_consecutive, remote_consecutive)
        local["cooldown_until"] = max(float(local.get("cooldown_until", 0) or 0), float(remote.get("cooldown_until", 0) or 0))
        local["quarantine_until"] = max(float(local.get("quarantine_until", 0) or 0), float(remote.get("quarantine_until", 0) or 0))
        if remote.get("last_error"):
            local["last_error"] = remote["last_error"]
            local["category"] = remote.get("category", local.get("category", ""))
        if remote_consecutive > local_consecutive and remote.get("last_operation"):
            local["last_operation"] = remote["last_operation"]
        elif not local.get("last_operation") and remote.get("last_operation"):
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
    return local
