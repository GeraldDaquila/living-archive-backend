"""Request-scoped Pinecone retrieval budget and monthly-egress circuit breaker."""
from __future__ import annotations

import contextvars
import threading
import time
from typing import Any

_REQUEST_STATE: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "use_pinecone_request_budget", default=None
)
_LOCK = threading.Lock()
_EGRESS_BLOCKED_MONTH: str | None = None
_EGRESS_LOGGED_MONTH: str | None = None

DEFAULT_REQUEST_CANDIDATE_BUDGET = 64
DEFAULT_PER_QUERY_CAP = 32


def _utc_month() -> str:
    return time.strftime("%Y-%m", time.gmtime())


def _is_monthly_egress_error(exc: BaseException) -> bool:
    message = str(exc).casefold()
    return (
        "egress limit" in message
        or ("1000000000 bytes" in message and "429" in message)
        or ("monthly" in message and "egress" in message and "429" in message)
    )


def _circuit_is_open() -> bool:
    global _EGRESS_BLOCKED_MONTH
    month = _utc_month()
    with _LOCK:
        if _EGRESS_BLOCKED_MONTH and _EGRESS_BLOCKED_MONTH != month:
            _EGRESS_BLOCKED_MONTH = None
        return _EGRESS_BLOCKED_MONTH == month


def _open_circuit(exc: BaseException) -> None:
    global _EGRESS_BLOCKED_MONTH, _EGRESS_LOGGED_MONTH
    month = _utc_month()
    with _LOCK:
        _EGRESS_BLOCKED_MONTH = month
        should_log = _EGRESS_LOGGED_MONTH != month
        _EGRESS_LOGGED_MONTH = month
    if should_log:
        print(
            "USE Pinecone retrieval circuit: OPEN; "
            f"reason=monthly_egress_exhausted; month={month}; "
            f"error={type(exc).__name__}",
            flush=True,
        )


class BoundedPineconeIndex:
    """Transparent Pinecone index proxy with bounded query response volume."""

    def __init__(self, index: Any, *, per_query_cap: int = 32) -> None:
        self._index = index
        self._per_query_cap = max(1, int(per_query_cap))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._index, name)

    def query(self, *args: Any, **kwargs: Any) -> Any:
        state = _REQUEST_STATE.get()
        if _circuit_is_open():
            if state is not None:
                state["circuit_skips"] += 1
            return {"matches": []}

        requested = kwargs.get("top_k")
        if not isinstance(requested, int) or requested < 1:
            return self._call_query(args, kwargs)

        allowed = min(requested, self._per_query_cap)
        if state is not None:
            remaining = max(0, int(state["remaining"]))
            if remaining == 0:
                state["budget_skips"] += 1
                return {"matches": []}
            allowed = min(allowed, remaining)
            state["remaining"] = remaining - allowed
            state["calls"] += 1
            state["requested_candidates"] += requested
            state["allowed_candidates"] += allowed
        elif allowed < requested:
            print(
                "USE Pinecone retrieval budget: "
                f"unscoped_query_clamped={requested}->{allowed}",
                flush=True,
            )

        bounded_kwargs = dict(kwargs)
        bounded_kwargs["top_k"] = allowed
        try:
            return self._index.query(*args, **bounded_kwargs)
        except Exception as exc:
            if _is_monthly_egress_error(exc):
                _open_circuit(exc)
                if state is not None:
                    state["quota_blocks"] += 1
                return {"matches": []}
            raise

    def _call_query(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        try:
            return self._index.query(*args, **kwargs)
        except Exception as exc:
            if _is_monthly_egress_error(exc):
                _open_circuit(exc)
                return {"matches": []}
            raise

    def fetch(self, *args: Any, **kwargs: Any) -> Any:
        state = _REQUEST_STATE.get()
        if _circuit_is_open():
            if state is not None:
                state["circuit_skips"] += 1
            return {"vectors": {}}
        try:
            return self._index.fetch(*args, **kwargs)
        except Exception as exc:
            if _is_monthly_egress_error(exc):
                _open_circuit(exc)
                if state is not None:
                    state["quota_blocks"] += 1
                return {"vectors": {}}
            raise


def install_pinecone_retrieval_budget(
    app: Any,
    index: Any,
    *,
    per_query_cap: int = DEFAULT_PER_QUERY_CAP,
    request_candidate_budget: int = DEFAULT_REQUEST_CANDIDATE_BUDGET,
) -> Any:
    """Wrap the live index; ASGI scope is installed by PineconeRequestBudgetMiddleware."""
    if index is None:
        print("USE Pinecone retrieval budget: index_unavailable=true", flush=True)
        return None
    wrapped = index if isinstance(index, BoundedPineconeIndex) else BoundedPineconeIndex(
        index, per_query_cap=per_query_cap
    )
    print(
        "USE Pinecone retrieval budget: index_wrapper_installed; "
        f"per_query_cap={per_query_cap}; "
        f"request_candidate_budget={request_candidate_budget}; "
        "monthly_egress_circuit_breaker=true",
        flush=True,
    )
    return wrapped


class PineconeRequestBudgetMiddleware:
    """Pure ASGI boundary; surrounds all custom request routers and FastAPI internals."""

    def __init__(self, app: Any, *, request_candidate_budget: int = 64) -> None:
        self.app = app
        self.request_candidate_budget = max(1, int(request_candidate_budget))

    def __getattr__(self, name: str) -> Any:
        return getattr(self.app, name)

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        state = {
            "remaining": self.request_candidate_budget,
            "calls": 0,
            "requested_candidates": 0,
            "allowed_candidates": 0,
            "budget_skips": 0,
            "circuit_skips": 0,
            "quota_blocks": 0,
        }
        token = _REQUEST_STATE.set(state)
        try:
            await self.app(scope, receive, send)
        finally:
            if any(state[key] for key in (
                "calls", "budget_skips", "circuit_skips", "quota_blocks"
            )):
                print(
                    "USE Pinecone request budget: "
                    f"path={scope.get('path', 'unknown')}; "
                    f"calls={state['calls']}; "
                    f"requested_candidates={state['requested_candidates']}; "
                    f"allowed_candidates={state['allowed_candidates']}; "
                    f"remaining={state['remaining']}; "
                    f"budget_skips={state['budget_skips']}; "
                    f"circuit_skips={state['circuit_skips']}; "
                    f"quota_blocks={state['quota_blocks']}",
                    flush=True,
                )
            _REQUEST_STATE.reset(token)


def _self_audit() -> None:
    class _FakeIndex:
        def __init__(self) -> None:
            self.calls: list[int] = []

        def query(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(int(kwargs["top_k"]))
            return {"matches": [{}] * int(kwargs["top_k"])}

    fake = _FakeIndex()
    proxy = BoundedPineconeIndex(fake, per_query_cap=10)
    token = _REQUEST_STATE.set({
        "remaining": 14, "calls": 0, "requested_candidates": 0,
        "allowed_candidates": 0, "budget_skips": 0, "circuit_skips": 0,
        "quota_blocks": 0,
    })
    try:
        first = proxy.query(vector=[0.0], top_k=100)
        second = proxy.query(vector=[0.0], top_k=100)
        third = proxy.query(vector=[0.0], top_k=1)
        assert len(first["matches"]) == 10
        assert len(second["matches"]) == 4
        assert third["matches"] == []
        assert fake.calls == [10, 4]
    finally:
        _REQUEST_STATE.reset(token)
    print("USE Pinecone retrieval budget self-audit: PASS", flush=True)


_self_audit()
