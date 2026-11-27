"""Request-local controls for isolated Gold Star matched-pair evaluation.

This module contains no credentials, visitor data, or persistent state.  The
context is scoped to the current execution context and must be entered with
`evaluation_context` and restored automatically on exit.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class GoldStarEvaluationContext:
    arm: str
    provider: str
    model: str
    candidate_id: str | None = None


_CONTEXT = ContextVar("gold_star_evaluation_context", default=None)


def current_evaluation_context():
    """Return the current immutable evaluation settings, or None."""
    return _CONTEXT.get()


@contextmanager
def evaluation_context(*, arm, provider, model, candidate_id=None):
    """Pin one evaluation arm to one exact provider/model for this context."""
    normalized_arm = str(arm or "").strip().casefold()
    normalized_provider = str(provider or "").strip()
    normalized_model = str(model or "").strip()
    if normalized_arm not in {"control", "treatment"}:
        raise ValueError("Evaluation arm must be control or treatment.")
    if not normalized_provider or not normalized_model:
        raise ValueError("Evaluation requires an exact provider and model pin.")
    normalized_candidate_id = str(candidate_id or "").strip() or None
    if normalized_candidate_id and normalized_arm != "treatment":
        raise ValueError("An evaluation-only candidate may be exposed only in the treatment arm.")
    value = GoldStarEvaluationContext(
        arm=normalized_arm,
        provider=normalized_provider,
        model=normalized_model,
        candidate_id=normalized_candidate_id,
    )
    token = _CONTEXT.set(value)
    try:
        yield value
    finally:
        _CONTEXT.reset(token)
