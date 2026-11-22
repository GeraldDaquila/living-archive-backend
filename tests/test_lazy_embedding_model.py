"""Regression tests for deferred local ONNX embedding initialization."""

from concurrent.futures import ThreadPoolExecutor
import threading
import time

import use_core


class _FakeVector:
    def tolist(self):
        return [0.125, 0.25, 0.5]


class _FakeEmbeddingModel:
    def embed(self, texts):
        assert len(texts) == 1
        return iter([_FakeVector()])


def test_module_import_does_not_load_fastembed_or_onnxruntime():
    import sys

    assert use_core.embedding_model is None
    assert "fastembed" not in sys.modules
    assert "onnxruntime" not in sys.modules


def test_embedding_model_is_initialized_only_when_embedding_is_requested(monkeypatch):
    created = []
    monkeypatch.setattr(use_core, "embedding_model", None)
    monkeypatch.setattr(
        use_core,
        "_create_embedding_model",
        lambda: created.append(_FakeEmbeddingModel()) or created[-1],
    )
    monkeypatch.setattr(use_core, "_log_embedding_runtime_diagnostic", lambda model: None)

    assert use_core.embedding_model is None
    assert use_core.generate_embedding("first actual embedding") == [0.125, 0.25, 0.5]
    assert len(created) == 1
    assert use_core.embedding_model is created[0]

    assert use_core.generate_embedding("second embedding") == [0.125, 0.25, 0.5]
    assert len(created) == 1


def test_concurrent_first_embedding_initializes_model_once(monkeypatch):
    created = []
    creation_lock = threading.Lock()

    def create_model():
        time.sleep(0.03)
        model = _FakeEmbeddingModel()
        with creation_lock:
            created.append(model)
        return model

    monkeypatch.setattr(use_core, "embedding_model", None)
    monkeypatch.setattr(use_core, "_create_embedding_model", create_model)
    monkeypatch.setattr(use_core, "_log_embedding_runtime_diagnostic", lambda model: None)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(use_core.generate_embedding, [f"query {i}" for i in range(8)]))

    assert results == [[0.125, 0.25, 0.5]] * 8
    assert len(created) == 1
    assert use_core.embedding_model is created[0]


def test_failed_lazy_initialization_preserves_embedding_failure_contract(monkeypatch):
    monkeypatch.setattr(use_core, "embedding_model", None)

    def fail_initialization():
        raise RuntimeError("simulated model initialization failure")

    monkeypatch.setattr(use_core, "_create_embedding_model", fail_initialization)
    monkeypatch.setattr(use_core, "_log_embedding_runtime_diagnostic", lambda model: None)

    assert use_core.generate_embedding("unavailable embedding") == []
    assert use_core.embedding_model is None
