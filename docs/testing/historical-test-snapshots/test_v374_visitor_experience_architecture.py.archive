from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "main.py"
MAIN = MAIN_PATH.read_text(encoding="utf-8")
CORE_PATH = ROOT / "use_core.py"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"


def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def test_v379_structural_visitor_experience_gate_exists():
    assert 'APP_VERSION = "v379"' in MAIN
    assert "def _visitor_experience_contract" in MAIN
    assert "def _frame_neutral_generation_documents" in MAIN
    assert "def _resource_frame_groups" in MAIN
    assert "def _call_original_with_calibrated_context" in MAIN
    assert "use_core.generate_llm_response = _v379_finalize" in MAIN
    assert "def _is_query_aligned_transition_doorway" in MAIN
    assert "app = use_core.app" in MAIN


def test_v379_does_not_use_transition_specific_answer_engine():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v379_finalize")
    source = ast.get_source_segment(MAIN, fn)
    assert "_guide_answer(" not in source
    assert "_call_original_with_calibrated_context" in source
    assert "_transition_retrieval_strategy" in source


def test_v379_preserves_unrequested_framework_authority_boundary():
    assert "avoid_unrequested_framework_as_primary" in MAIN
    assert "allow_interpretive_evidence_as_non_authoritative" in MAIN
    assert "preserve_epistemic_opening" in MAIN


def test_v379_open_transition_falls_back_to_original_generation_instead_of_unavailable():
    fn = ast.get_source_segment(
        MAIN,
        next(n for n in ast.parse(MAIN).body if isinstance(n, ast.FunctionDef) and n.name == "_v379_finalize"),
    )
    assert "if not aligned:" in fn
    assert "return _original_generate_llm_response(*args, **kwargs)" in fn
    assert "is_open_transition" in fn


def test_v379_open_transition_does_not_wholesale_reject_specialized_evidence():
    start = MAIN.index("def _is_query_aligned_transition_doorway")
    end = MAIN.index("def _merge_recovered_documents")
    gate = MAIN[start:end]
    assert "if clusters[\"worldview\"] or _is_specialized_framework_resource(doc):" not in gate


def test_v379_does_not_treat_generic_scientific_evidence_as_a_framework():
    assert '"academic"' not in MAIN
    signal_section = MAIN.split("def _resource_frame_groups", 1)[0]
    assert "scientific" not in signal_section


def test_v379_preserves_protected_core_and_runtime_identity():
    assert f'EXPECTED_CORE_BLOB_SHA = "{EXPECTED_CORE_BLOB_SHA}"' in MAIN
    assert "hashlib.sha1(f\"blob {len(data)}\\0\".encode() + data).hexdigest()" in MAIN
    assert CORE_PATH.exists()
    assert _git_blob_sha256(CORE_PATH.read_bytes()) == EXPECTED_CORE_BLOB_SHA


def test_v379_source_compiles():
    ast.parse(MAIN)
