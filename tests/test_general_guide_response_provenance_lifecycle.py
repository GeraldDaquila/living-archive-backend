"""Regression tests for preserving real provider provenance through final assembly."""
import ast
from pathlib import Path


def _basic_inquiry_ast():
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_basic_inquiry_response"
    )
    return source, function


def test_basic_inquiry_preserves_composition_until_an_explicit_deterministic_override():
    _, function = _basic_inquiry_ast()
    assignments = {"composition_result": [], "deterministic_result": []}
    for node in ast.walk(function):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in assignments:
                if isinstance(node.value, ast.Constant) and node.value.value is None:
                    assignments[target.id].append(node.lineno)

    composition_initializers = assignments["composition_result"]
    deterministic_initializers = assignments["deterministic_result"]
    assert len(composition_initializers) == 2, (
        "Composition may be initialized once and cleared only at the explicit "
        "trust/community deterministic override."
    )
    assert len(deterministic_initializers) == 1, (
        "The deterministic result must be initialized once before routing."
    )

    first_compose = min(
        node.lineno for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "compose"
    )
    metric_line = next(
        node.lineno for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        and isinstance(node.args[0] if node.args else None, ast.Constant)
        and isinstance(node.args[0].value, str)
        and "USE RESPONSE METRIC:" in node.args[0].value
    )
    first_init, explicit_override_clear = sorted(composition_initializers)
    assert first_init < first_compose < explicit_override_clear < metric_line
    assert deterministic_initializers[0] < first_compose

    source, _ = _basic_inquiry_ast()
    source_lines = source.splitlines()
    assert any(
        "deterministic_result = {" in line
        for line in source_lines[max(0, explicit_override_clear - 16):explicit_override_clear - 1]
    ), "The only late composition reset must follow an explicit deterministic result assignment."


def test_llm_attribution_requires_the_final_answer_to_match_the_provider_candidate():
    source, _ = _basic_inquiry_ast()
    assert "_llm_candidate_text = _sanitize_basic_inquiry_response(" in source
    assert "_final_response_text = _sanitize_basic_inquiry_response(str(response or \"\")" in source
    assert "_final_response_text == _llm_candidate_text" in source
    assert '_provider_name = "deterministic_final_boundary"' in source
