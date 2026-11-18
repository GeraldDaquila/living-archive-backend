import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _assignment_value(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node.value
    raise AssertionError(f"{name} assignment not found")


def test_living_archive_navigator_is_an_explicit_provider_gateway_operation():
    source = (ROOT / "provider_gateway_service.py").read_text()
    allowed = _assignment_value(source, "ALLOWED_OPERATIONS")
    operation_names = {
        item.value for item in ast.walk(allowed)
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    }
    assert "living_archive_navigator" in operation_names


def test_living_archive_navigator_has_a_provider_bank_capability_and_budget():
    source = (ROOT / "provider_bank.py").read_text()
    assert '"living_archive_navigator": 900' in source
    assert '"living_archive_navigator": frozenset({"json_object", "long_context", "reasoning", "composition"})' in source


def test_living_archive_navigator_has_a_bounded_provider_timeout_and_candidate_count():
    source = (ROOT / "provider_bank.py").read_text()
    tree = ast.parse(source)
    timeout_function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_provider_call_timeout"
    )
    navigator_timeout = any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "operation"
        and any(isinstance(op, ast.Eq) for op in node.test.ops)
        and any(
            isinstance(value, ast.Constant) and value.value == "living_archive_navigator"
            for value in node.test.comparators
        )
        and any(
            isinstance(stmt, ast.Return)
            and isinstance(stmt.value, ast.Constant)
            and stmt.value.value == 4.0
            for stmt in node.body
        )
        for node in ast.walk(timeout_function)
    )
    assert navigator_timeout
    assert 'elif operation == "living_archive_navigator":\n        operation_attempt_cap = 3' in source
