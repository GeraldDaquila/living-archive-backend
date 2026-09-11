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


def test_v339_identity_and_boundary_exist():
    source = MAIN.read_text(encoding="utf-8")
    assert 'APP_VERSION = "v339"' in source
    assert "_v339_canonical_recommendation_doorway" in source
    assert "EXPECTED_CORE_SOURCE_SHA256" in source


def test_v339_final_presenter_enforces_canonical_link():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "_v339_canonical_recommendation_doorway")
    assert "_adjudicate_recommendation_resource" in fn
    assert "canonical_link = f\"[{title}]({url})\"" in fn
    assert "A useful place to begin is " in fn


def test_v339_constructor_calls_doorway_after_link_normalization():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "_v336_construct_visitor_answer")
    normalize_pos = fn.find("normalize_link_presentation")
    doorway_pos = fn.find("_v339_canonical_recommendation_doorway")
    assert normalize_pos >= 0
    assert doorway_pos > normalize_pos


def test_v339_runtime_seams_remain_exported():
    source = MAIN.read_text(encoding="utf-8")
    assert "app = use_core.app" in source
    assert 'if __name__ == "__main__":' in source
