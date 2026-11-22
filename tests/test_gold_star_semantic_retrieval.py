"""Behavioral tests for semantic Gold Star retrieval and abstention."""
import gold_star_lessons as lessons
import gold_star_semantic_retrieval as semantic
import general_guide_composition as composition
import pytest


def test_semantic_paraphrase_can_retrieve_without_two_word_overlap(monkeypatch):
    target = next(
        item for item in lessons._LESSONS
        if item["id"] == "gs-2026-11-21-transformation-rebranding-structural-change"
    )
    query = "When is renewal just cosmetic rebranding?"
    query_terms = lessons._concept_terms(query)
    assert len(query_terms & target["signature_terms"]) < 2
    monkeypatch.setattr(semantic, "semantic_index_ready", lambda: True)
    monkeypatch.setattr(
        semantic, "rank_semantic_lessons",
        lambda _query, candidates: {item["id"]: (0.86 if item["id"] == target["id"] else 0.20) for item in candidates},
    )
    result = lessons.select_lesson_candidates(query)
    assert result
    assert result[0]["benchmark_id"] == target["id"]
    assert result[0]["exact"] is False


def test_semantic_similarity_without_subject_anchor_is_rejected(monkeypatch):
    monkeypatch.setattr(semantic, "semantic_index_ready", lambda: True)
    monkeypatch.setattr(
        semantic, "rank_semantic_lessons",
        lambda _query, candidates: {item["id"]: 0.91 for item in candidates},
    )
    result = lessons.select_lesson_candidates("How do tides affect coastal ecosystems?")
    assert result == []

def test_semantic_retrieval_reuses_the_shared_use_core_model(monkeypatch):
    import sys
    import types

    class FakeModel:
        def __init__(self):
            self.calls = []

        def embed(self, texts, batch_size=256):
            self.calls.append((list(texts), batch_size))
            return iter([[1.0] + [0.0] * 383 for _ in texts])

    shared = FakeModel()
    fake_use_core = types.ModuleType("use_core")
    fake_use_core._get_embedding_model = lambda: shared
    monkeypatch.setitem(sys.modules, "use_core", fake_use_core)
    semantic._model.cache_clear()
    semantic._lesson_vectors.cache_clear()
    try:
        assert semantic._model() is shared
        lessons_for_test = [{
            "id": "test-lesson",
            "query": "A reviewed test question",
            "known_theme": "A test theme",
            "reasoning_family": "A test reasoning family",
            "variants": [],
        }]
        monkeypatch.setattr(semantic, "_LESSON_SOURCE", lambda: lessons_for_test)
        vectors = semantic._lesson_vectors()
        assert list(vectors) == ["test-lesson"]
        assert len(vectors["test-lesson"]) == 384
        assert shared.calls[0][1] == 32

        scores = semantic.rank_semantic_lessons("a test query", lessons_for_test)
        assert scores == {"test-lesson": 1.0}
        assert shared.calls[1][1] == 1
    finally:
        semantic._lesson_vectors.cache_clear()
        semantic._model.cache_clear()



def test_cold_semantic_selector_requests_warmup_without_blocking(monkeypatch):
    requested = []
    monkeypatch.setattr(semantic, "semantic_index_ready", lambda: False)
    monkeypatch.setattr(
        semantic,
        "request_semantic_index_warmup",
        lambda: requested.append(True) or True,
    )
    monkeypatch.setattr(
        semantic,
        "rank_semantic_lessons",
        lambda *_args, **_kwargs: pytest.fail("cold semantic model must not load in the visitor path"),
    )

    result = lessons.select_lesson_candidates("When is renewal just cosmetic rebranding?")

    assert result == []
    assert requested == [True]


def test_cold_semantic_warmup_starts_only_after_provider_route(monkeypatch):
    events = []
    composition._COMPOSITION_CACHE.clear()
    monkeypatch.setattr(semantic, "semantic_index_ready", lambda: False)
    monkeypatch.setattr(
        semantic,
        "request_semantic_index_warmup",
        lambda: events.append("warmup_requested") or True,
    )
    monkeypatch.setattr(
        semantic,
        "start_requested_semantic_warmup",
        lambda: events.append("warmup_started") or True,
    )
    monkeypatch.setattr(
        composition,
        "_gold_star_active_quality_contribution",
        lambda query: lessons.active_quality_contribution(query),
    )
    monkeypatch.setattr(composition, "_registered_exact_gold_standard", lambda _query: None)
    monkeypatch.setattr(
        composition,
        "route_with_model_bank",
        lambda **_kwargs: events.append("provider_route") or None,
    )

    composition.compose(
        use_core=None,
        query="When is renewal just cosmetic rebranding?",
        context_data={},
    )

    assert events[:3] == [
        "warmup_requested",
        "provider_route",
        "warmup_started",
    ]



def _reset_semantic_warmup_state():
    semantic._WARMUP_REQUESTED = False
    semantic._WARMUP_THREAD = None


def test_background_warmup_materializes_index_and_marks_ready(monkeypatch):
    _reset_semantic_warmup_state()
    ready = {"value": False}
    monkeypatch.setattr(semantic, "semantic_index_ready", lambda: ready["value"])

    def materialize():
        ready["value"] = True
        return {"reviewed-lesson": [1.0]}

    monkeypatch.setattr(semantic, "_lesson_vectors", materialize)

    assert semantic.request_semantic_index_warmup() is True
    assert semantic.start_requested_semantic_warmup() is True
    thread = semantic._WARMUP_THREAD
    assert thread is not None
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert ready["value"] is True
    assert semantic.semantic_index_ready() is True
    assert semantic._WARMUP_THREAD is None
    assert semantic._WARMUP_REQUESTED is False


def test_failed_background_warmup_clears_thread_and_allows_retry(monkeypatch):
    _reset_semantic_warmup_state()
    ready = {"value": False}
    attempts = {"count": 0}
    monkeypatch.setattr(semantic, "semantic_index_ready", lambda: ready["value"])

    def materialize():
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("simulated embedding initialization failure")
        ready["value"] = True
        return {"reviewed-lesson": [1.0]}

    monkeypatch.setattr(semantic, "_lesson_vectors", materialize)

    assert semantic.request_semantic_index_warmup() is True
    assert semantic.start_requested_semantic_warmup() is True
    first_thread = semantic._WARMUP_THREAD
    assert first_thread is not None
    first_thread.join(timeout=5)

    assert not first_thread.is_alive()
    assert ready["value"] is False
    assert semantic._WARMUP_THREAD is None

    # A failed materialization must not poison readiness or suppress retries.
    assert semantic.request_semantic_index_warmup() is True
    assert semantic.start_requested_semantic_warmup() is True
    second_thread = semantic._WARMUP_THREAD
    assert second_thread is not None
    second_thread.join(timeout=5)

    assert not second_thread.is_alive()
    assert attempts["count"] == 2
    assert ready["value"] is True
    assert semantic.semantic_index_ready() is True
    assert semantic._WARMUP_THREAD is None
    assert semantic._WARMUP_REQUESTED is False
