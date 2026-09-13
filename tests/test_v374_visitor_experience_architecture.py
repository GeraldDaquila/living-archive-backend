from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_v374_structural_visitor_experience_gate_exists():
    assert 'APP_VERSION = "v374"' in MAIN
    assert "def _visitor_experience_contract" in MAIN
    assert "def _frame_neutral_generation_documents" in MAIN
    assert "def _resource_frame_groups" in MAIN
    assert "def _call_original_with_calibrated_context" in MAIN
    assert "use_core.generate_llm_response = _v374_finalize" in MAIN


def test_v374_does_not_use_transition_specific_answer_engine():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v374_finalize")
    source = ast.get_source_segment(MAIN, fn)
    assert "_guide_answer(" not in source
    assert "_call_original_with_calibrated_context" in source
    assert "_transition_retrieval_strategy" in source


def test_v374_protects_unrequested_composite_frameworks():
    assert "_requested_frame_groups" in MAIN
    assert "_resource_frame_groups(doc) & requested_groups" in MAIN
    assert "preserve_epistemic_opening" in MAIN
    assert "avoid_unrequested_framework_as_primary" in MAIN


def test_v374_preserves_protected_core():
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
