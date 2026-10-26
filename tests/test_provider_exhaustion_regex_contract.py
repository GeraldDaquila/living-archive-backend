"""Runtime boundary tests for provider-exhaustion definition recovery."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_exact_institutional_memory_question_matches_runtime_recovery_gate():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    anchor = source.index("# Shared definition recovery must replace the weak legacy fallback")
    end = source.index("if is_harm_repair_question(query):", anchor)
    start = source.rfind("        if re.match(", 0, anchor)
    block = source[start:end]
    pattern_match = re.search(r'r"\\(\?i\)([^"]+)"', block)
    whitespace_match = re.search(r're.sub\(r"([^"]+)",', block)
    assert pattern_match
    assert whitespace_match
    query = "What is institutional memory, and why does it matter?"
    normalized = re.sub(whitespace_match.group(1), " ", query).strip()
    assert re.match("(?i)" + pattern_match.group(1), normalized)


def test_recovery_regressions_are_explicitly_invoked_by_composition_ci():
    workflow = (ROOT / ".github" / "workflows" / "general-guide-composition-contract.yml").read_text(encoding="utf-8")
    assert "tests/test_shared_definition_exhaustion_recovery.py" in workflow
    assert "tests/test_provider_exhaustion_regex_contract.py" in workflow
