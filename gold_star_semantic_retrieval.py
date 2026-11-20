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
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=_MODEL_NAME)


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
    vectors = list(model.embed(texts))
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
    query_text = str(query)
    if hasattr(model, "query_embed"):
        query_embedding = next(iter(model.query_embed([query_text])))
    else:
        query_embedding = next(iter(model.embed([query_text])))
    query_vector = _unit(query_embedding)
    vectors = _lesson_vectors()
    return {
        str(item["id"]): sum(
            left * right for left, right in zip(query_vector, vectors[str(item["id"])])
        )
        for item in candidates
        if str(item.get("id")) in vectors
    }
