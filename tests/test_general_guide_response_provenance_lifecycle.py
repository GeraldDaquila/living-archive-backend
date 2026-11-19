"""Regression tests for preserving real provider provenance through final assembly."""
import ast
from pathlib import Path


def test_basic_inquiry_initializes_provenance_once_before_routing_and_never_resets_it():
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_basic_inquiry_response"
    )

    assignments = {"composition_result": [], "deterministic_result": []}
    for node in ast.walk(function):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if isinstance(node, ast.Assign):
            targets = node.targets
        else:
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in assignments:
                assignments[target.id].append((node.lineno, value))

    for name, entries in assignments.items():
        none_initializers = [
            lineno for lineno, value in entries
            if isinstance(value, ast.Constant) and value.value is None
        ]
        assert len(none_initializers) == 1, (
            f"{name} must have exactly one initialization; later resets erase "
            "the actual provider/deterministic result before provenance is emitted."
        )

    first_compose = min(
        node.lineno for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "compose"
    )
    first_metric = next(
        node.lineno for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        and isinstance(node.args[0] if node.args else None, ast.Constant)
        and isinstance(node.args[0].value, str)
        and "USE RESPONSE METRIC:" in node.args[0].value
    )
    for name, entries in assignments.items():
        initializer = next(
            lineno for lineno, value in entries
            if isinstance(value, ast.Constant) and value.value is None
        )
        assert initializer < first_compose < first_metric
