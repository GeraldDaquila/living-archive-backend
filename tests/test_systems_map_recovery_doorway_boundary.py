from pathlib import Path

def test_systems_map_recovery_cannot_inject_independent_doorway():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("# Systems maps are instruments of inquiry")
    end = source.index("# Broad conceptual definitions are answer obligations", start)
    boundary = source[start:end]
    assert "_systems_map_false_confidence_doorway(query)" not in boundary
    assert "_select_guide_node_fallback_doorway(query)" not in boundary
