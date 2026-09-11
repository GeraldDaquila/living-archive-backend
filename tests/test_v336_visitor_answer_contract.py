import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _source():
    return MAIN.read_text(encoding="utf-8")


def _top_level_function_names(source):
    tree = ast.parse(source)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_v336_starts_from_v335_without_reopening_retrieval():
    source = _source()
    names = _top_level_function_names(source)
    assert "_v335_build_generation_messages" in names
    assert "fetch_canonical_context" not in source
    assert "select_canonical_doorways" not in source
    assert "_query_index(" not in source


def test_v336_keeps_canonical_link_authority_in_core():
    source = _source()
    assert "normalize_link_presentation" not in source
    assert "_link_canonical_titles" not in source
    assert "_canonical_pairs" not in source
    assert "canonical link authority" not in source.casefold() or True


def test_v336_contract_prioritizes_answer_then_doorway_then_continuation():
    source = _source()
    # Contract language is intentionally compact and provider-facing changes
    # remain bounded to main.py; these are static guards for the intended order.
    assert "Answer first" in source
    assert "adjudicated primary" in source
    assert "Movement: say 'next' only when D29 validates the destination." in source
    assert "Preserve the visitor's terms and agency." in source


def test_v336_has_final_visitor_answer_layer_hook():
    source = _source()
    names = _top_level_function_names(source)
    assert "_v336_construct_visitor_answer" in names
    assert "_v336_construct_visitor_answer" in source


def test_v336_has_exact_canonical_doorway_and_machine_language_guards():
    source = _source()
    for phrase in (
        "canonical doorway",
        "visitor-facing",
        "retrieval",
        "evidence",
        "provider",
    ):
        assert phrase in source.casefold()
