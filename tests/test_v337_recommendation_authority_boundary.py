"""v337 recommendation-authority boundary regression tests."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"

PRIMARY = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
SECONDARY = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"


def _source(path):
    return path.read_text(encoding="utf-8")


def _function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"missing function: {name}")


def test_v337_final_wrapper_routes_through_authority_boundary():
    source = _source(MAIN)
    authority = _function(source, "_v337_apply_recommendation_authority")
    wrapper = _function(source, "_v336_run_generation_boundary")
    finalizer = _function(source, "_v339_finalize_generation_response")
    assert "_original_recommendation_output_authority" in authority
    assert "_original_recommendation_resource_identity" in authority
    assert "_adjudicate_recommendation_resource" in authority
    assert "_v336_construct_visitor_answer" in wrapper
    assert "_v336_construct_visitor_answer" in finalizer
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in source


def test_v337_recommendation_benchmark_identity_is_present_at_wrapper_boundary():
    source = _source(MAIN)
    assert PRIMARY in source
    assert SECONDARY in source


def test_protected_core_is_not_assumed_to_expose_v337_provider_helpers():
    source = _source(CORE)
    assert "_adjudicate_recommendation_resource" in source
