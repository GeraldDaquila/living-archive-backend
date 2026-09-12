from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _source():
    return MAIN.read_text(encoding="utf-8")


def _function_source(source, name):
    tree = ast.parse(source)
    node = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == name
    )
    return ast.get_source_segment(source, node)


def test_recommendation_boundary_has_deterministic_nonempty_fallback():
    source = _source()
    text = _function_source(source, "_v338_final_answer_boundary")
    assert "if primary:" in text
    assert "A useful place to begin is" in text


def test_recommendation_constructor_does_not_return_model_query_echo():
    source = _source()
    text = _function_source(source, "_v336_construct_visitor_answer")
    assert "if use_core._is_recommendation_question(user_query):" in text
    assert "return answer" in text


def test_recommendation_finalizer_extracts_context_before_provider():
    source = _source()
    text = _function_source(source, "_v339_finalize_generation_response")
    assert "_context_blocks_from_kwargs(args, kwargs)" in text
    assert "_v338_final_answer_boundary(" in text
    assert "provider generation skipped" in text
