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


def test_v382_identity_and_protected_core():
    assert 'APP_VERSION = "v382"' in MAIN
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v382-transition-selection-continuation"' in MAIN
    assert f'EXPECTED_CORE_BLOB_SHA = "{EXPECTED_CORE_BLOB_SHA}"' in MAIN
    assert CORE_PATH.exists()
    assert _git_blob_sha256(CORE_PATH.read_bytes()) == EXPECTED_CORE_BLOB_SHA


def test_v382_open_transition_uses_only_aligned_generation_context():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v382_finalize")
    source = ast.get_source_segment(MAIN, fn)
    transition_source = source.split("if is_open_transition:", 1)[1]
    assert "calibrated_docs = sorted(aligned" in transition_source
    assert "calibrated_context = _rebuild_context_blocks(calibrated_docs)" in transition_source
    assert "_call_original_with_calibrated_context" in transition_source
    assert "_frame_neutral_generation_documents" not in transition_source


def test_v382_open_transition_fails_closed_when_no_aligned_evidence_exists():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v382_finalize")
    source = ast.get_source_segment(MAIN, fn)
    transition_source = source.split("if is_open_transition:", 1)[1]
    assert "if not aligned:" in transition_source
    assert "_frame_neutral_evidence_unavailable_response" in transition_source
    assert "return _original_generate_llm_response(*args, **kwargs)" not in transition_source


def test_v382_source_compiles():
    ast.parse(MAIN)
