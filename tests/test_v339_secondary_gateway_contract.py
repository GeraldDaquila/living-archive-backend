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


def test_secondary_pathways_are_role_diverse():
    source = _source()
    text = _function_source(source, "_select_secondary_pathways")
    assert "used_roles" in text
    assert "role in used_roles" in text


def test_secondary_roles_are_question_oriented():
    source = _source()
    text = _function_source(source, "_secondary_role")
    assert "continuity and what may endure" in text
    assert "a broader exploration of afterlife and reincarnation possibilities" in text


def test_runtime_seam_remains_intact():
    source = _source()
    assert "app = use_core.app" in source
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in source
    assert "if __name__ == \"__main__\":" in source
