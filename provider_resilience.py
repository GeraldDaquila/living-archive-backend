"""Bounded self-healing state machine for the USE provider stack.

This module owns provider/model health state only. It never edits code, prompts,
credentials, specialist contracts, or safety policy.
"""

import time

CONTRACT_VERSION = "v1"

HEALTHY = "healthy"
DEGRADED = "degraded"
OPEN = "open"
HALF_OPEN = "half_open"

TRANSIENT_COOLDOWN = {
    "rate_limited": 60.0,
    "network_failure": 30.0,
    "provider_failure": 30.0,
    "unavailable": 30.0,
    "invalid_provider_response": 30.0,
}
PERMANENT_COOLDOWN = {
    "authentication": 900.0,
    "quota_or_billing": 1800.0,
    "request_too_large": 1800.0,
    "model_unavailable": 3600.0,
    "terms_required": 3600.0,
    "structured_output_contract": 3600.0,
    "free_tier_daily_quota": 86400.0,
}

def new_state(provider, model):
    return {
        "provider": provider,
        "model": model,
        "state": HEALTHY,
        "failures": 0,
        "consecutive_failures": 0,
        "probe_successes": 0,
        "probe_in_flight": False,
        "cooldown_until": 0.0,
        "quarantine_until": 0.0,
        "last_error": "",
        "last_success": 0.0,
        "last_failure": 0.0,
        "category": "",
    }

def blocked(state, now=None):
    """Return whether this candidate is unavailable without mutating probe ownership."""
    now = time.time() if now is None else float(now)
    state_name = str(state.get("state") or HEALTHY)
    until = max(
        float(state.get("cooldown_until", 0) or 0),
        float(state.get("quarantine_until", 0) or 0),
    )
    if state_name == OPEN:
        if now < until:
            return True
        state["state"] = HALF_OPEN
    return state_name == HALF_OPEN and bool(state.get("probe_in_flight"))

def acquire_probe(state):
    """Allow exactly one recovery probe when a circuit is half-open."""
    if str(state.get("state") or HEALTHY) != HALF_OPEN:
        return True
    if state.get("probe_in_flight"):
        return False
    state["probe_in_flight"] = True
    return True

def record_failure(state, category, message, *, now=None, retry_after=None):
    now = time.time() if now is None else float(now)
    category = str(category or "provider_failure")
    state["failures"] = int(state.get("failures", 0)) + 1
    state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1
    state["last_failure"] = now
    state["last_error"] = str(message or "")[:500]
    state["category"] = category
    state["probe_in_flight"] = False

    if category == "rate_limited":
        delay = max(30.0, float(retry_after or 60.0))
    elif category == "free_tier_daily_quota":
        delay = min(86400.0, max(60.0, float(retry_after or PERMANENT_COOLDOWN[category])))
    elif category in PERMANENT_COOLDOWN:
        delay = PERMANENT_COOLDOWN[category]
    else:
        base = TRANSIENT_COOLDOWN.get(category, 30.0)
        exponent = min(int(state["consecutive_failures"]) - 1, 4)
        delay = min(300.0, base * (2 ** max(0, exponent)))

    if category in PERMANENT_COOLDOWN:
        state["quarantine_until"] = now + delay
        state["cooldown_until"] = 0.0
    else:
        state["cooldown_until"] = now + delay
        state["quarantine_until"] = 0.0
    state["state"] = OPEN
    return delay

def record_success(state, *, now=None):
    now = time.time() if now is None else float(now)
    state.update({
        "state": HEALTHY,
        "failures": 0,
        "consecutive_failures": 0,
        "probe_successes": int(state.get("probe_successes", 0)) + 1,
        "probe_in_flight": False,
        "cooldown_until": 0.0,
        "quarantine_until": 0.0,
        "last_error": "",
        "last_success": now,
        "category": "",
    })

def state_summary(state):
    return {
        "state": str(state.get("state") or HEALTHY),
        "failures": int(state.get("failures", 0)),
        "consecutive_failures": int(state.get("consecutive_failures", 0)),
        "probe_successes": int(state.get("probe_successes", 0)),
        "cooldown_until": float(state.get("cooldown_until", 0) or 0),
        "quarantine_until": float(state.get("quarantine_until", 0) or 0),
        "last_error": str(state.get("last_error") or ""),
        "last_success": float(state.get("last_success", 0) or 0),
        "last_failure": float(state.get("last_failure", 0) or 0),
        "category": str(state.get("category") or ""),
    }

def aggregate_provider_health(states):
    """Summarize model health without hiding individual model failures."""
    if not states:
        return HEALTHY
    names = [str(x.get("state") or HEALTHY) for x in states]
    if all(name == OPEN for name in names):
        return OPEN
    if any(name in {DEGRADED, OPEN, HALF_OPEN} for name in names):
        return DEGRADED
    return HEALTHY
