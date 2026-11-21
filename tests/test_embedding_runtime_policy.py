import use_core


def test_onnx_cpu_mem_arena_defaults_to_existing_onnx_runtime_behavior():
    assert use_core._parse_onnx_cpu_mem_arena_enabled(None) is True
    assert use_core._parse_onnx_cpu_mem_arena_enabled("") is True


def test_onnx_cpu_mem_arena_can_be_disabled_explicitly():
    for value in ("0", "false", "False", "no", "off", "disabled"):
        assert use_core._parse_onnx_cpu_mem_arena_enabled(value) is False


def test_onnx_cpu_mem_arena_can_be_enabled_explicitly():
    for value in ("1", "true", "TRUE", "yes", "on", "enabled"):
        assert use_core._parse_onnx_cpu_mem_arena_enabled(value) is True


def test_invalid_onnx_cpu_mem_arena_value_preserves_safe_default():
    assert use_core._parse_onnx_cpu_mem_arena_enabled("maybe") is True


def test_use_core_wires_memory_arena_policy_without_changing_embedding_model():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "use_core.py").read_text(encoding="utf-8")
    assert 'model_name="BAAI/bge-small-en-v1.5"' in source
    assert "enable_cpu_mem_arena=EMBEDDING_ENABLE_CPU_MEM_ARENA" in source
    assert 'os.getenv("USE_ONNX_ENABLE_CPU_MEM_ARENA")' in source
    assert "cpu_mem_arena_enabled=" in source
