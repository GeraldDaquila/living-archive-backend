"""Semantic retrieval for governed Gold Star structural lessons.

Uses the canonical 384-dimensional BAAI/bge-small-en-v1.5 model already
declared in the USE runtime dependencies. Embeddings are cached per process;
only approved lesson metadata is embedded, never exemplar answers.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Any

_MODEL_NAME = "BAAI/bge-small-en-v1.5"


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
