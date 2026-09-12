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


def test_risk_bearing_secondary_material_is_suppressed_for_sensitive_nonrisk_queries():
    text = _function_source(_source(), "_select_secondary_pathways")
    assert "profile.get(\"sensitive\")" in text
    assert "score -= 8" in text
    assert "suicid|suicidal ideation|self-harm|overdose|abuse|coercion" in text


def test_secondary_roles_are_differentiated_before_selection():
    text = _function_source(_source(), "_select_secondary_pathways")
    assert "used_roles" in text
    assert "if role in used_roles" in text


def test_deployment_seam_remains_intact():
    source = _source()
    assert "app = use_core.app" in source
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in source


def test_protected_core_blob_remains_pinned():
    source = _source()
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in source
