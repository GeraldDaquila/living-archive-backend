import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"

PRIMARY = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
SECONDARY = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"


def _function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"missing function: {name}")


def test_v339_identity_and_fit_boundary_exist():
    source = MAIN.read_text(encoding="utf-8")
    assert 'APP_VERSION = "v339"' in source
    assert "_v338_recommendation_fit_sentence" in source
    assert "_v338_build_recommendation_answer" in source
    assert "_v339_canonical_recommendation_doorway" in source
    assert "do not retract the recommendation" in source


def test_v339_fit_sentence_is_evidence_bound():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "_v338_recommendation_fit_sentence")
    assert "primary.get(\"text\"" in fn
    assert "grief, loss, and death" in fn
    assert "several complementary perspectives" in fn


def test_v339_recommendation_answer_removes_contradictory_retraction():
    source = MAIN.read_text(encoding="utf-8")
    fn = _function(source, "_v338_build_recommendation_answer")
    assert "There is no supplied form" in fn
    assert "There is no supplied (?:canonical )?(?:essay|advice|resource)" in fn


def test_v339_benchmark_resources_remain_named():
    source = MAIN.read_text(encoding="utf-8")
    assert PRIMARY in source
    assert SECONDARY in source
