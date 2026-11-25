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
    # The full pytest process may already have initialized embeddings in an
    # earlier test. Verify the import contract in a fresh interpreter so this
    # assertion is independent of test order and shared module state.
    import subprocess
    import sys

    probe = (
        "import sys; "
        "import use_core; "
        "assert use_core.embedding_model is None; "
        "assert 'fastembed' not in sys.modules; "
        "assert 'onnxruntime' not in sys.modules"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


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


def test_onnx_cpu_mem_arena_policy_defaults_to_existing_behavior():
    assert use_core._parse_onnx_cpu_mem_arena_enabled(None) is True
    assert use_core._parse_onnx_cpu_mem_arena_enabled("") is True
    assert use_core._parse_onnx_cpu_mem_arena_enabled("maybe") is True


def test_onnx_cpu_mem_arena_policy_accepts_explicit_disable_and_enable():
    for value in ("0", "false", "False", "no", "off", "disabled"):
        assert use_core._parse_onnx_cpu_mem_arena_enabled(value) is False
    for value in ("1", "true", "TRUE", "yes", "on", "enabled"):
        assert use_core._parse_onnx_cpu_mem_arena_enabled(value) is True


def test_lazy_embedding_factory_passes_memory_arena_policy_without_changing_model(monkeypatch):
    import sys
    import types

    captured = {}

    class FakeTextEmbedding:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    fake_fastembed = types.ModuleType("fastembed")
    fake_fastembed.TextEmbedding = FakeTextEmbedding
    monkeypatch.setitem(sys.modules, "fastembed", fake_fastembed)
    monkeypatch.setattr(use_core, "EMBEDDING_ENABLE_CPU_MEM_ARENA", False)

    result = use_core._create_embedding_model()

    assert isinstance(result, FakeTextEmbedding)
    assert captured == {
        "model_name": "BAAI/bge-small-en-v1.5",
        "threads": 1,
        "enable_cpu_mem_arena": False,
    }
