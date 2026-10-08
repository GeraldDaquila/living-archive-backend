"""USE boundary resilience primitives.

These primitives protect the seams around The Guide without owning reasoning,
provider selection, HRN composition, or visitor-facing language.

The design principle is simple:
- keep the last known good authoritative boundary when an external authority
  temporarily disappears;
- never treat stale authority as fresh authority;
- never silently replace specialist-owned material with Guide-generated prose;
- make boundary state observable without exposing it to visitors.
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

CONTRACT_VERSION = "v1"

FRESH = "fresh"
STALE = "stale"
UNAVAILABLE = "unavailable"


@dataclass
class BoundarySnapshot:
    value: Any
    fetched_at: float
    state: str = FRESH
    failure_at: float = 0.0
    failure_count: int = 0
    last_error: str = ""

    @property
    def age_seconds(self) -> float:
        return max(0.0, time.time() - self.fetched_at) if self.fetched_at else float("inf")


class StaleAuthorityCache:
    """Bounded last-known-good cache for an external authoritative registry.

    A stale value may keep the system operational, but callers can distinguish
    stale from fresh and refuse authority-sensitive actions while stale.
    """

    def __init__(
        self,
        *,
        max_stale_seconds: float = 3600.0,
        failure_retry_seconds: float = 30.0,
    ) -> None:
        self.max_stale_seconds = float(max_stale_seconds)
        self.failure_retry_seconds = float(failure_retry_seconds)
        self._snapshot: Optional[BoundarySnapshot] = None

    def get(self, loader: Callable[[], Any]) -> tuple[Any, str]:
        now = time.time()

        if self._snapshot is not None:
            age = now - self._snapshot.fetched_at
            if self._snapshot.state == FRESH and age < self.max_stale_seconds:
                return copy.deepcopy(self._snapshot.value), FRESH
            if (
                self._snapshot.failure_at
                and now - self._snapshot.failure_at < self.failure_retry_seconds
            ):
                if age < self.max_stale_seconds:
                    self._snapshot.state = STALE
                    return copy.deepcopy(self._snapshot.value), STALE
                self._snapshot.state = UNAVAILABLE
                return [], UNAVAILABLE

        try:
            value = loader()
            self._snapshot = BoundarySnapshot(
                value=copy.deepcopy(value),
                fetched_at=now,
                state=FRESH,
            )
            return copy.deepcopy(value), FRESH
        except Exception as exc:
            if self._snapshot is not None:
                age = now - self._snapshot.fetched_at
                self._snapshot.failure_at = now
                self._snapshot.failure_count += 1
                self._snapshot.last_error = str(exc)[:500]
                if age < self.max_stale_seconds:
                    self._snapshot.state = STALE
                    return copy.deepcopy(self._snapshot.value), STALE
            self._snapshot = (
                self._snapshot
                or BoundarySnapshot(value=[], fetched_at=0.0, state=UNAVAILABLE)
            )
            self._snapshot.state = UNAVAILABLE
            self._snapshot.failure_at = now
            self._snapshot.last_error = str(exc)[:500]
            return [], UNAVAILABLE

    def snapshot(self) -> dict[str, Any]:
        item = self._snapshot
        if item is None:
            return {
                "state": UNAVAILABLE,
                "age_seconds": None,
                "failure_count": 0,
                "last_error": "",
            }
        return {
            "state": item.state,
            "age_seconds": round(item.age_seconds, 2),
            "failure_count": item.failure_count,
            "last_error": item.last_error,
        }


def preserve_specialist_payload(
    payload: Mapping[str, Any],
    *,
    required_keys: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Deep-copy specialist-owned material without rewriting its semantics.

    This is deliberately not a normalizer. It does not rewrite strings,
    collapse fields, select canonical resources, or generate replacement text.
    """

    if not isinstance(payload, Mapping):
        raise TypeError("specialist payload must be a mapping")

    missing = [
        key for key in required_keys
        if key not in payload
    ]
    if missing:
        raise ValueError(
            "specialist payload missing required fields: " + ", ".join(missing)
        )

    return copy.deepcopy(dict(payload))
