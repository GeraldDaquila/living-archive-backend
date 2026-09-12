from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _function_source(source, name):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(source, node)


def test_recommendation_architecture_preserves_existing_chunking_and_links():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert '"\\n\\n".join' in text
    assert "_resource_link(doc)" in text
    assert "A gentle place to begin is" in text


def test_recommendation_architecture_names_human_reality_and_foothold():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "grief" in text.casefold()
    assert "A gentle place to begin is" in text


def test_recommendation_architecture_preserves_epistemic_boundaries_and_agency():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "leaving uncertainty intact" in text
    assert "Take what feels useful" in text


def test_recommendation_architecture_remains_reflection_gateway():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "nearby paths worth exploring" in text
    assert "secondary" in text


def test_recommendation_secondary_titles_are_presentation_clean():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_resource_link")
    assert "re.sub" in text
    assert "return f\"[{title}]({url})\"" in text
