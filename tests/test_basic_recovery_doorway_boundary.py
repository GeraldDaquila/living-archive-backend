import ast
from pathlib import Path


def test_basic_inquiry_recovery_cannot_run_independent_cross_scale_doorway():
    source = Path("main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_basic_inquiry_response"
    )
    calls = {
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_cross_scale_canonical_doorway" not in calls
    assert "recommendation_canonical_primary" in ast.get_source_segment(source, function)
