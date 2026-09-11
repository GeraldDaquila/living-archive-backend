import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"

PRIMARY = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"


def _function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"missing function: {name}")


def test_recommendation_doorway_never_returns_title_only_when_primary_has_url():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "_v339_canonical_recommendation_doorway")
    assert 'canonical_link = f"[{title}]({url})"' in fn
    assert "if not title or not url:" in fn
    assert "return f\"{prefix}{canonical_link}." in fn


def test_recommendation_presenter_is_only_final_constructor_for_provider_paths():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "_v336_construct_visitor_answer")
    assert fn.count("_v339_canonical_recommendation_doorway(") == 1
    assert fn.find("normalize_link_presentation") < fn.find("_v339_canonical_recommendation_doorway")


def test_current_benchmark_primary_contract_is_embedded():
    source = MAIN.read_text(encoding="utf-8")
    assert PRIMARY in source
    assert PRIMARY_URL in source
