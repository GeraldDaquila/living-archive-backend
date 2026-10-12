"""Bounded provider quota admission for USE inference calls.

This layer limits in-flight work per provider/model and optionally enforces
operator-configured RPM, TPM, and TPD budgets. It is deliberately fail-fast:
a saturated lane is skipped in favor of an independent provider instead of
creating an unbounded queue or retry storm.

State is process-local. Cross-instance cooldown/health sharing remains owned by
provider_health_store; globally atomic quota reservations require a shared
reservation primitive and are not falsely claimed by this module.
"""
from __future__ import annotations

import json
import os
import threading
from time import monotonic as _monotonic
from typing import Any

CONTRACT_VERSION = "v1"
_LOCK = threading.RLock()
_BUCKETS: dict[str, dict[str, float]] = {}
_ACTIVE_PROVIDER: dict[str, int] = {}
_ACTIVE_MODEL: dict[str, int] = {}
_COUNTERS = {
    "admitted": 0,
    "rejected_concurrency": 0,
    "rejected_rpm": 0,
    "rejected_tpm": 0,
    "rejected_tpd": 0,
    "released": 0,
}


class QuotaAdmissionDenied(RuntimeError):
    """A local admission limit rejected work before it reached the provider."""

    def __init__(self, provider: str, model: str, reason: str, retry_after: float = 1.0):
        super().__init__(f"provider admission denied: {reason}")
        self.provider = provider
        self.model = model
        self.reason = reason
        self.retry_after = max(0.1, float(retry_after))


def _int_env(name: str, default: int, minimum: int = 1, maximum: int = 1_000_000) -> int:
    try:
        value = int(str(os.getenv(name, "") or default).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in str(value).upper()).strip("_")


def estimate_tokens(messages: Any, max_tokens: int) -> int:
    """Conservative token estimate: roughly one token per four UTF-8-ish chars."""
    try:
        rendered = json.dumps(messages, ensure_ascii=False, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        rendered = str(messages)
    input_estimate = max(1, (len(rendered) + 3) // 4)
    return input_estimate + max(1, int(max_tokens or 1))


def _bucket_check(key: str, limit: int, cost: float, period: float, now: float) -> tuple[bool, float]:
    bucket = _BUCKETS.get(key)
    if bucket is None:
        bucket = {"tokens": float(limit), "updated": now}
        _BUCKETS[key] = bucket
    elapsed = max(0.0, now - float(bucket["updated"]))
    bucket["tokens"] = min(float(limit), float(bucket["tokens"]) + elapsed * float(limit) / period)
    bucket["updated"] = now
    if cost > limit:
        return False, period
    if bucket["tokens"] + 1e-9 < cost:
        wait = (cost - bucket["tokens"]) * period / float(limit)
        return False, max(0.1, wait)
    return True, 0.0


def _bucket_consume(key: str, cost: float) -> None:
    _BUCKETS[key]["tokens"] = max(0.0, float(_BUCKETS[key]["tokens"]) - float(cost))


class Reservation:
    def __init__(self, provider: str, model: str, token_estimate: int):
        self.provider = provider
        self.model = model
        self.token_estimate = int(token_estimate)
        self._released = False

    def release(self) -> None:
        if self._released:
            return
        with _LOCK:
            _ACTIVE_PROVIDER[self.provider] = max(0, _ACTIVE_PROVIDER.get(self.provider, 1) - 1)
            _ACTIVE_MODEL[self.provider + ":" + self.model] = max(
                0, _ACTIVE_MODEL.get(self.provider + ":" + self.model, 1) - 1
            )
            self._released = True
            _COUNTERS["released"] += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False


def reserve(provider: str, model: str, messages: Any, max_tokens: int) -> Reservation:
    """Admit one call atomically or fail fast without poisoning provider health."""
    provider = str(provider or "").strip().lower()
    model = str(model or "").strip()
    if not provider or not model:
        raise QuotaAdmissionDenied(provider, model, "invalid_lane", 1.0)
    estimate = estimate_tokens(messages, max_tokens)
    provider_key = provider
    model_key = provider + ":" + model
    provider_slug = _slug(provider)
    model_slug = _slug(model)
    now = _monotonic()

    with _LOCK:
        max_provider = _int_env("USE_QUOTA_MAX_INFLIGHT_PROVIDER", 3)
        max_model = _int_env("USE_QUOTA_MAX_INFLIGHT_MODEL", 2)
        if _ACTIVE_PROVIDER.get(provider_key, 0) >= max_provider:
            _COUNTERS["rejected_concurrency"] += 1
            raise QuotaAdmissionDenied(provider, model, "provider_concurrency_cap", 1.0)
        if _ACTIVE_MODEL.get(model_key, 0) >= max_model:
            _COUNTERS["rejected_concurrency"] += 1
            raise QuotaAdmissionDenied(provider, model, "model_concurrency_cap", 1.0)

        # Provider-account budgets are shared by all configured models of that
        # provider within this process. Model-specific token budgets can be
        # layered on top where a provider publishes per-model limits.
        budgets = (
            ("rpm", f"USE_QUOTA_{provider_slug}_RPM", 60.0, 1.0),
            ("tpm", f"USE_QUOTA_{provider_slug}_TPM", 60.0, float(estimate)),
            ("tpd", f"USE_QUOTA_{provider_slug}_TPD", 86400.0, float(estimate)),
        )
        planned_buckets = []
        for kind, env_name, period, cost in budgets:
            raw = str(os.getenv(env_name) or "").strip()
            if not raw:
                continue
            try:
                limit = int(raw)
            except ValueError:
                continue
            if limit <= 0:
                continue
            bucket_key = provider_key + ":" + kind
            ok, retry_after = _bucket_check(bucket_key, limit, cost, period, now)
            if not ok:
                counter = "rejected_" + kind
                _COUNTERS[counter] += 1
                raise QuotaAdmissionDenied(provider, model, kind + "_budget_exhausted", retry_after)
            planned_buckets.append((bucket_key, cost))

        model_tpm_name = f"USE_QUOTA_{provider_slug}_{model_slug}_TPM"
        raw_model_tpm = str(os.getenv(model_tpm_name) or "").strip()
        if raw_model_tpm:
            try:
                model_tpm = int(raw_model_tpm)
            except ValueError:
                model_tpm = 0
            if model_tpm > 0:
                model_bucket_key = model_key + ":tpm"
                ok, retry_after = _bucket_check(model_bucket_key, model_tpm, float(estimate), 60.0, now)
                if not ok:
                    _COUNTERS["rejected_tpm"] += 1
                    raise QuotaAdmissionDenied(provider, model, "model_tpm_budget_exhausted", retry_after)
                planned_buckets.append((model_bucket_key, float(estimate)))

        # Commit all token-bucket deductions only after every budget check passes.
        for bucket_key, cost in planned_buckets:
            _bucket_consume(bucket_key, cost)

        _ACTIVE_PROVIDER[provider_key] = _ACTIVE_PROVIDER.get(provider_key, 0) + 1
        _ACTIVE_MODEL[model_key] = _ACTIVE_MODEL.get(model_key, 0) + 1
        _COUNTERS["admitted"] += 1
    return Reservation(provider, model, estimate)


def snapshot() -> dict[str, Any]:
    with _LOCK:
        return {
            "contract_version": CONTRACT_VERSION,
            "scope": "process_local_admission_with_optional_provider_and_model_budgets",
            "cross_instance_atomic_reservations": False,
            "defaults": {
                "max_inflight_per_provider": _int_env("USE_QUOTA_MAX_INFLIGHT_PROVIDER", 3),
                "max_inflight_per_model": _int_env("USE_QUOTA_MAX_INFLIGHT_MODEL", 2),
            },
            "configured_budgets": {
                key: int(value)
                for key, value in os.environ.items()
                if key.startswith("USE_QUOTA_") and value.strip().isdigit()
            },
            "active_provider_calls": dict(_ACTIVE_PROVIDER),
            "active_model_calls": dict(_ACTIVE_MODEL),
            "counters": dict(_COUNTERS),
        }


def _reset_for_tests() -> None:
    """Reset module-local state; test-only helper."""
    with _LOCK:
        _BUCKETS.clear()
        _ACTIVE_PROVIDER.clear()
        _ACTIVE_MODEL.clear()
        for key in _COUNTERS:
            _COUNTERS[key] = 0
