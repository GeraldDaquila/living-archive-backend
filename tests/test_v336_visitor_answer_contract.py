from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _source():
    return MAIN.read_text(encoding="utf-8")


def _top_level_function_names(source):
    tree = ast.parse(source)
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_v387_current_visitor_answer_entrypoint():
    source = _source()
    names = _top_level_function_names(source)
    assert "_parse_context_documents" in names
    assert "_build_sensitive_recommendation_answer" in names
    assert "_v387_finalize" in names
    assert "fetch_canonical_context" not in source
    assert "select_canonical_doorways(" not in source
    assert "_query_index(" not in source


def test_v387_keeps_canonical_link_authority_in_core():
    source = _source()
    assert "def normalize_link_presentation" not in source
    assert "def _link_canonical_titles" not in source
    assert "def _canonical_pairs" not in source
    assert "use_core" in source


def test_v387_answer_contract_preserves_authority_terms():
    source = _source().casefold()
    for phrase in ("retrieval", "evidence", "provider", "canonical"):
        assert phrase in source
