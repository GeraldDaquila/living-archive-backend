"""Runtime boundary tests for provider-exhaustion definition recovery."""
import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_exact_institutional_memory_question_matches_runtime_recovery_gate():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    patterns = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name) or node.func.value.id != "re":
            continue
        if node.func.attr != "match" or len(node.args) < 2:
            continue
        pattern_node, query_node = node.args[:2]
        if not isinstance(pattern_node, ast.Constant) or not isinstance(pattern_node.value, str):
            continue
        pattern = pattern_node.value
        if not pattern.startswith("(?i)^what is ") or "and why does it matter" not in pattern:
            continue
        if not isinstance(query_node, ast.Call) or not isinstance(query_node.func, ast.Attribute):
            continue
        if not isinstance(query_node.func.value, ast.Name) or query_node.func.value.id != "re":
            continue
        if query_node.func.attr != "sub" or len(query_node.args) < 2:
            continue
        whitespace_pattern = query_node.args[0]
        if isinstance(whitespace_pattern, ast.Constant) and whitespace_pattern.value == r"\s+":
            patterns.append((pattern, whitespace_pattern.value))

    assert patterns, "Could not locate the shared definition recovery gate in main.py"
    query = "What is institutional memory, and why does it matter?"
    assert any(
        re.match(pattern, re.sub(whitespace_pattern, " ", query).strip())
        for pattern, whitespace_pattern in patterns
    )


def test_recovery_regressions_are_explicitly_invoked_by_composition_ci():
    workflow = (ROOT / ".github" / "workflows" / "general-guide-composition-contract.yml").read_text(encoding="utf-8")
    assert "tests/test_shared_definition_exhaustion_recovery.py" in workflow
    assert "tests/test_provider_exhaustion_regex_contract.py" in workflow
