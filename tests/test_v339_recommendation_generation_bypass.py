from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _source():
    return MAIN.read_text(encoding="utf-8")


def _function_source(source, name):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(source, node)


def test_recommendation_finalizer_checks_deterministic_boundary_before_provider():
    source = _source()
    text = _function_source(source, "_v339_finalize_generation_response")
    assert "if use_core._is_recommendation_question(user_query):" in text
    assert "recommendation_answer = _v338_final_answer_boundary(" in text
    assert text.index("recommendation_answer = _v338_final_answer_boundary(") < text.index("value = _original_generate_llm_response(")
    assert "deterministic canonical doorway used; provider generation skipped" in text


def test_recommendation_boundary_can_build_answer_without_model_output():
    source = _source()
    text = _function_source(source, "_v338_final_answer_boundary")
    assert "value = str(answer or \"\").strip()" in text
    assert "if primary:" in text
    assert "A useful place to begin is" in text
