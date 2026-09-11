import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"missing function: {name}")


def test_generate_wrapper_owns_final_recommendation_boundary():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "_v339_finalize_generation_response")
    assert "_original_generate_llm_response" in fn
    assert "use_core._is_recommendation_question" in fn
    assert "_v336_construct_visitor_answer" in fn


def test_public_generate_llm_response_routes_through_v339_finalizer():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "generate_llm_response")
    assert "_v339_finalize_generation_response" in fn
    assert "_original_generate_llm_response" not in fn


def test_core_generate_fallback_is_not_the_public_recommendation_exit():
    source = MAIN.read_text(encoding="utf-8")
    finalizer = _function(source, "_v339_finalize_generation_response")
    assert "return _v336_construct_visitor_answer(" in finalizer

