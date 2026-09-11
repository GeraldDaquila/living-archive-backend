"""v337 recommendation-authority boundary regression tests."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"

GRIEF_QUERY = (
    "What advise or essay from the Living Archive that you can recommend "
    "for someone who is grieving from the death of a love one?"
)
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


def test_v336_generation_path_enforces_recommendation_authority():
    source = _source(CORE)
    run_attempt = _function(source, "_run_generation_attempt")
    assert "_enforce_recommendation_output_authority" in run_attempt
    assert "_enforce_recommendation_resource_identity" in run_attempt
    recovery = _function(source, "_run_provider_completion_recovery")
    assert "_enforce_recommendation_resource_identity" in recovery


def test_v337_final_wrapper_routes_through_authority_boundary():
    source = _source(MAIN)
    authority = _function(source, "_v337_apply_recommendation_authority")
    wrapper = _function(source, "_v336_run_generation_boundary")
    finalizer = _function(source, "_v339_finalize_generation_response")
    assert "_original_recommendation_output_authority" in authority
    assert "_original_recommendation_resource_identity" in authority
    assert "_v337_apply_recommendation_authority" in _function(source, "_v338_final_answer_boundary")
    assert "_deterministic_provider_fallback" in finalizer or "_original_generate_llm_response" in finalizer
    assert "_v336_construct_visitor_answer" in wrapper
    assert "_v336_construct_visitor_answer" in finalizer


def test_v337_recommendation_benchmark_identity_is_present():
    source = _source(CORE)
    assert PRIMARY in source
    assert SECONDARY in source
    assert "assert winner is target" in source
    assert "recommendation-to-doorway coherence" in source
