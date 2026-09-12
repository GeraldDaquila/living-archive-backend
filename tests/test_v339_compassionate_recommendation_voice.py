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


def test_recommendation_answer_has_compassionate_voice_constructor():
    source = _source()
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "specific piece that speaks directly to this kind of loss" in text
    assert "grief, loss, and death" in text
    assert "without forcing certainty" in text
    assert "rather than asking grief to become something you simply resolve" in text


def test_recommendation_answer_preserves_canonical_doorway():
    source = _source()
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "[{title}]({url})" in text
    assert "A useful place to begin is" in text


def test_recommendation_voice_is_not_model_generated_at_final_boundary():
    source = _source()
    text = _function_source(source, "_v339_finalize_generation_response")
    assert "deterministic compassionate answer used; provider generation skipped" in text
