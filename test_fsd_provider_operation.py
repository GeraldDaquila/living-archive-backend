"""Static contract checks for the isolated FSD Provider Bank lane.

These checks intentionally avoid importing the production provider runtime or
loading credentials/network clients in the lightweight FSD CI job.
"""
import ast
from pathlib import Path


def _literal(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "frozenset":
        return frozenset(ast.literal_eval(node.args[0]))
    if isinstance(node, ast.Dict):
        return {_literal(key): _literal(value) for key, value in zip(node.keys, node.values)}
    return ast.literal_eval(node)


def _assignment(path, name):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return _literal(node.value)
    raise AssertionError(f"{name} assignment not found in {path}")


def test_gateway_explicitly_allows_fsd_report_operation():
    allowed = _assignment("provider_gateway_service.py", "ALLOWED_OPERATIONS")
    assert "fsd_report_composition" in allowed


def test_fsd_report_lane_has_independent_capability_policy():
    requirements = _assignment("provider_bank.py", "OPERATION_REQUIREMENTS")
    assert requirements["fsd_report_composition"] == frozenset({
        "json_object", "long_context", "composition", "reasoning"
    })


def test_fsd_report_lane_has_bounded_completion_budget():
    floors = _assignment("provider_bank.py", "OPERATION_TOKEN_FLOORS")
    assert floors["fsd_report_composition"] == 1100
    assert floors["general_guide_composition"] == 900
