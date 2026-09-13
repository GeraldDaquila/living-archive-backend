from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def _top_level_function_names(source):
    tree = ast.parse(source)
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_v387_preserves_runtime_seam_and_current_hook():
    names = _top_level_function_names(MAIN)
    assert "_parse_context_documents" in names
    assert "_build_sensitive_recommendation_answer" in names
    assert "_v387_finalize" in names
    assert "app = use_core.app" in MAIN
    assert "use_core.generate_llm_response = _v387_finalize" in MAIN


def test_v387_keeps_link_authority_in_core():
    assert "def normalize_link_presentation" not in MAIN
    assert "def _link_canonical_titles" not in MAIN
    assert "def _canonical_pairs" not in MAIN
    assert "use_core" in MAIN


def test_v387_keeps_answer_contract_terms():
    for phrase in ("visitor-facing", "retrieval", "evidence", "provider", "canonical"):
        assert phrase.casefold() in MAIN.casefold()
