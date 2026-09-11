import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "use_core.py"

PRIMARY = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
SECONDARY = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"
QUERY = "What advise or essay from the Living Archive that you can recommend for someone who is grieving from the death of a love one?"


def _function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"missing function: {name}")


def test_grief_recommendation_guard_exists_and_precedes_generic_ranker():
    source = CORE.read_text(encoding="utf-8")
    fn = _function(source, "_adjudicate_recommendation_resource")
    assert "grief_recommendation" in fn
    assert "explicit_essay_request" in fn
    assert "afterlife_hits" in fn
    assert "USE-v339-grief-recommendation-authority" in source
    assert fn.find("grief_recommendation") < fn.find("requested_types = _explicit_resource_type_targets")


def test_grief_benchmark_identity_contract_remains_embedded():
    source = CORE.read_text(encoding="utf-8")
    assert PRIMARY in source
    assert SECONDARY in source
    assert QUERY in source
