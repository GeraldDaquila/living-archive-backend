import ast
from pathlib import Path


def _core_source():
    return Path(__file__).resolve().parents[1].joinpath("use_core.py").read_text(encoding="utf-8")


def _function_node(name):
    tree = ast.parse(_core_source())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function: {name}")


def _function_source(name):
    source = _core_source().splitlines()
    node = _function_node(name)
    return "\n".join(source[node.lineno - 1 : node.end_lineno])


def test_v337_branch_preserves_v336_runtime_seam():
    main = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "v336"' in main
    assert "_v336_construct_visitor_answer" in main
    assert "normalize_link_presentation" in main


def test_recommendation_adjudicator_prioritizes_directness_before_broad_overlap():
    source = _function_source("_adjudicate_recommendation_resource")
    directness_pos = source.index("directness_title")
    synthesis_pos = source.index("synthesis[0]")
    subject_pos = source.index("subject[3]")
    assert directness_pos < synthesis_pos
    assert directness_pos < subject_pos
    assert "essay_match" in source
    assert "requested_types" in source


def test_grief_fixture_is_present_and_targets_loss_essay():
    source = _core_source()
    assert "What advise or essay from the Living Archive that you can recommend" in source
    assert "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom" in source
    assert "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences" in source


def test_v337_does_not_modify_retrieval_or_link_functions():
    source = _core_source()
    assert "def _v337_" not in source
    assert "def normalize_link_presentation" in source
    assert "def select_canonical_doorways" in source
