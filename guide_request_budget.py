"""Shared request-wide budget for ordinary Guide composition and repairs."""
from __future__ import annotations

from time import monotonic as _monotonic

# The ordinary Guide request includes retrieval, one composition route, and
# downstream visitor-boundary validation. Keep one absolute deadline across
# these stages rather than restarting a full provider budget for every repair.
REQUEST_BUDGET_SECONDS = 24.0
PROVIDER_CALL_MINIMUM_SECONDS = 1.0
REPAIR_RESERVE_SECONDS = 6.0


def remaining_seconds(deadline_monotonic: float, *, now: float | None = None) -> float:
    """Return non-negative time left in an absolute monotonic deadline."""
    current = _monotonic() if now is None else float(now)
    return max(0.0, float(deadline_monotonic) - current)


def bounded_provider_timeout(
    base_timeout: float | None,
    deadline_monotonic: float | None,
    *,
    now: float | None = None,
) -> float | None:
    """Clamp a provider call to the shared deadline; zero means do not start."""
    if deadline_monotonic is None:
        return base_timeout
    remaining = remaining_seconds(deadline_monotonic, now=now)
    if remaining < PROVIDER_CALL_MINIMUM_SECONDS:
        return 0.0
    if base_timeout is None:
        return remaining
    return min(max(0.0, float(base_timeout)), remaining)


def can_attempt_repair(
    deadline_monotonic: float,
    *,
    already_attempted: bool = False,
    now: float | None = None,
) -> bool:
    """Allow at most one extra composition and only if its bounded call fits."""
    if already_attempted:
        return False
    return remaining_seconds(deadline_monotonic, now=now) >= REPAIR_RESERVE_SECONDS
