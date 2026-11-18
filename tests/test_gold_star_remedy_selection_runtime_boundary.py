"""Runtime-boundary regressions for Gold Star remedy-selection questions."""

import ast
from pathlib import Path

import general_guide_composition as composition

ROOT = Path(__file__).resolve().parents[1]
QUERY = (
    "How should USE distinguish a recurring weakness that deserves a new Gold Star "
    "from a weakness better addressed through improved retrieval, source metadata, "
    "or deterministic logic?"
)


def test_basic_inquiry_intercepts_remedy_selection_before_any_retrieval():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_basic_inquiry_response"
    )
    calls = []
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                calls.append((func.attr, node.lineno))
            elif isinstance(func, ast.Name):
                calls.append((func.id, node.lineno))
    recovery_line = next(
        line for name, line in calls
        if name == "_gold_star_remedy_selection_recovery"
    )
    retrieval_line = next(
        line for name, line in calls
        if name == "fetch_canonical_context"
    )
    assert recovery_line < retrieval_line
    assert "retrieval_invoked=false, provider_invoked=false" in source


def test_early_recovery_payload_is_complete_and_explicitly_suppresses_unverified_doorway():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert '"processing": "gold_star_remedy_selection_recovery"' in source
    assert '"response": _answer' in source
    assert '"recommendation": None' in source
    assert '"canonical_doorway": None' in source
    assert '"doorway_omission_reason": "no_verified_direct_archive_continuation"' in source
    assert '"llm_invoked": False' in source
    assert '"recovery": "gold_star_remedy_selection"' in source


def test_runtime_recovery_still_matches_exact_visitor_question():
    result = composition._gold_star_remedy_selection_recovery(QUERY)
    assert result is not None
    assert result["response"].startswith("USE should create a Gold Star only when")
    assert len([p for p in result["response"].split("\n\n") if p.strip()]) == 3
