"""Semantic retrieval for governed Gold Star structural lessons.

Uses the canonical 384-dimensional BAAI/bge-small-en-v1.5 model already
declared in the USE runtime dependencies. Embeddings are cached per process;
only approved lesson metadata is embedded, never exemplar answers.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Any
import logging
import os
from pathlib import Path
import threading

_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_LOG = logging.getLogger(__name__)
_WARMUP_LOCK = threading.Lock()
_WARMUP_REQUESTED = False
_WARMUP_THREAD: threading.Thread | None = None


def _warmup_enabled() -> bool:
    """Require an explicit operator opt-in for memory-intensive model loading."""
    return os.getenv("GOLD_STAR_SEMANTIC_WARMUP_ENABLED", "").strip().casefold() in {
        "1", "true", "yes", "on", "enabled"
    }


def _memory_snapshot() -> str:
    """Return container memory counters without adding a runtime dependency."""
    values = []
    for label, path in (
        ("current_bytes", "/sys/fs/cgroup/memory.current"),
        ("limit_bytes", "/sys/fs/cgroup/memory.max"),
        ("legacy_current_bytes", "/sys/fs/cgroup/memory/memory.usage_in_bytes"),
        ("legacy_limit_bytes", "/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ):
        try:
            raw = Path(path).read_text(encoding="ascii").strip()
            if raw and raw != "max":
                values.append(f"{label}={int(raw)}")
        except (OSError, ValueError):
            continue
    return " ".join(values) if values else "unavailable"


@lru_cache(maxsize=1)
def _model():
    # Reuse the process-wide USE embedding model. Creating a second FastEmbed /
    # ONNX session here makes the first unseen Gold Star query pay for two model
    # instances in a 512 MiB service. The shared loader is lazy and keeps the
    # canonical model/thread configuration in one place.
    from use_core import _get_embedding_model
    return _get_embedding_model()


def _unit(vector):
    values = [float(value) for value in vector]
    norm = sum(value * value for value in values) ** 0.5
    if not norm:
        raise ValueError("Embedding model returned a zero vector")
    return [value / norm for value in values]


@lru_cache(maxsize=1)
def _lesson_vectors():
    lessons = _LESSON_SOURCE()
    model = _model()
    texts = [
        " | ".join((
            str(item.get("query") or ""),
            str(item.get("known_theme") or ""),
            str(item.get("reasoning_family") or ""),
            " ".join(item.get("variants") or []),
        ))
        for item in lessons
    ]
    vectors = list(model.embed(texts, batch_size=32))
    return {
        str(item["id"]): _unit(vector)
        for item, vector in zip(lessons, vectors)
    }


def _LESSON_SOURCE():
    # Import lazily to avoid a circular import during Gold Star registry load.
    from gold_star_lessons import _LESSONS
    return _LESSONS


def semantic_index_ready() -> bool:
    """Return whether the process has a fully materialized semantic lesson index."""
    return _lesson_vectors.cache_info().currsize > 0


def request_semantic_index_warmup() -> bool:
    """Mark a cold semantic index for warming after the current visitor route."""
    global _WARMUP_REQUESTED
    if not _warmup_enabled():
        _LOG.warning(
            "Gold Star semantic warmup disabled by safety gate; "
            "set GOLD_STAR_SEMANTIC_WARMUP_ENABLED=1 only after memory-safe validation"
        )
        return False
    if semantic_index_ready():
        return False
    with _WARMUP_LOCK:
        if _WARMUP_THREAD is not None and _WARMUP_THREAD.is_alive():
            return False
        _WARMUP_REQUESTED = True
    return True


def _warm_semantic_index() -> None:
    global _WARMUP_THREAD
    try:
        _LOG.info(
            "Gold Star semantic warmup initialization starting memory=%s",
            _memory_snapshot(),
        )
        _lesson_vectors()
        _LOG.info(
            "Gold Star semantic index background warmup completed memory=%s",
            _memory_snapshot(),
        )
    except Exception as exc:
        _LOG.warning(
            "Gold Star semantic index background warmup failed: %s",
            type(exc).__name__,
        )
    finally:
        with _WARMUP_LOCK:
            _WARMUP_THREAD = None


def start_requested_semantic_warmup() -> bool:
    """Start a previously requested warmup without blocking the visitor response."""
    global _WARMUP_REQUESTED, _WARMUP_THREAD
    with _WARMUP_LOCK:
        if not _warmup_enabled():
            _WARMUP_REQUESTED = False
            _LOG.warning("Gold Star semantic warmup start blocked by safety gate")
            return False
        if not _WARMUP_REQUESTED or semantic_index_ready():
            _WARMUP_REQUESTED = False
            return False
        if _WARMUP_THREAD is not None and _WARMUP_THREAD.is_alive():
            return False
        _WARMUP_REQUESTED = False
        thread = threading.Thread(
            target=_warm_semantic_index,
            name="gold-star-semantic-index-warmup",
            daemon=True,
        )
        _WARMUP_THREAD = thread
        try:
            thread.start()
        except Exception:
            _WARMUP_THREAD = None
            _WARMUP_REQUESTED = True
            raise
    _LOG.info("Gold Star semantic index background warmup started")
    return True


def rank_semantic_lessons(query: str, candidates: List[Dict[str, Any]]) -> Dict[str, float]:
    """Return cosine similarity for current candidates using the canonical BGE model."""
    if not candidates:
        return {}
    model = _model()
    query_text = "Represent this sentence for searching relevant passages: " + str(query)
    query_vector = _unit(next(iter(model.embed([query_text], batch_size=1))))
    vectors = _lesson_vectors()
    return {
        str(item["id"]): sum(
            left * right for left, right in zip(query_vector, vectors[str(item["id"])])
        )
        for item in candidates
        if str(item.get("id")) in vectors
    }
