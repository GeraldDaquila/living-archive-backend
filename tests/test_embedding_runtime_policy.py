from embedding_runtime_policy import parse_onnx_cpu_mem_arena_enabled


def test_onnx_cpu_mem_arena_defaults_to_existing_onnx_runtime_behavior():
    assert parse_onnx_cpu_mem_arena_enabled(None) is True
    assert parse_onnx_cpu_mem_arena_enabled("") is True


def test_onnx_cpu_mem_arena_can_be_disabled_explicitly():
    for value in ("0", "false", "False", "no", "off", "disabled"):
        assert parse_onnx_cpu_mem_arena_enabled(value) is False


def test_onnx_cpu_mem_arena_can_be_enabled_explicitly():
    for value in ("1", "true", "TRUE", "yes", "on", "enabled"):
        assert parse_onnx_cpu_mem_arena_enabled(value) is True


def test_invalid_onnx_cpu_mem_arena_value_preserves_safe_default():
    assert parse_onnx_cpu_mem_arena_enabled("maybe") is True
