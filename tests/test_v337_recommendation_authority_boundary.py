"""v337 recommendation-authority boundary regression tests."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"

GRIEF_QUERY = (
    "What advise or essay from the Living Archive that you can recommend "
    "for someone who is grieving from the death of a love one?"
)
PRIMARY = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
SECONDARY = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"


def _main_source():
    return MAIN.read_text(encoding="utf-8")


def _function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"missing function: {name}")


def test_recommendation_task_contract_requires_primary_early():
    source = _function(_main_source(), "_v335_compact_response_contract")
    assert "Recommendation: name the adjudicated primary early" in source


def test_v336_constructor_has_context_available_for_authoritative_identity():
    source = _function(_main_source(), "_v336_construct_visitor_answer")
    assert "canonical_link_context or context_blocks" in source
    assert "normalize_link_presentation" in source


def test_grief_benchmark_identity_is_present_in_repository_audit():
    source = (ROOT / "use_core.py").read_text(encoding="utf-8")
    assert PRIMARY in source
    assert SECONDARY in source
    assert "assert winner is target" in source
    assert "recommendation-to-doorway coherence" in source
