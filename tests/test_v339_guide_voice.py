from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _function_source(source, name):
    tree = ast.parse(source)
    node = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == name
    )
    return ast.get_source_segment(source, node)


def test_recommendation_voice_is_companionable_not_classificatory():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "For someone grieving" in text
    assert "without forcing certainty" in text
    assert "The Living Archive has a specific piece" in text
    assert "direct fit because" not in text


def test_recommendation_answer_does_not_repeat_primary_as_context():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "including {section}" in text
    assert "{title}" not in text.split("context_line", 1)[1]
