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


def test_secondary_pathways_have_evidence_ranked_roles():
    source = _source()
    text = _function_source(source, "_select_secondary_pathways")
    assert "score" in text
    assert "meaning" in text
    assert "continuity" in text


def test_reflection_gateway_exposes_question_opening_roles():
    source = _source()
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "what question this opens" in text
    assert "_secondary_role" in source


def test_secondary_gateway_links_remain_canonical():
    source = _source()
    text = _function_source(source, "_resource_link")
    assert "return f\"[{title}]({url})\"" in text


def test_primary_is_not_repeated_as_secondary_gateway():
    source = _source()
    text = _function_source(source, "_select_secondary_pathways")
    assert "title.casefold() in seen" in text
