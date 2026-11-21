"""Environment policy for bounded ONNX Runtime memory use."""


def parse_onnx_cpu_mem_arena_enabled(value: str | None) -> bool:
    """Parse the FastEmbed ONNX CPU memory-arena setting.

    Preserve ONNX Runtime's current default unless an explicit false value is
    supplied. Unknown values fail open to the default so a typo cannot silently
    change the production embedding path.
    """
    if value is None:
        return True
    normalized = value.strip().casefold()
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    return True
