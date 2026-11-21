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


def test_v381_identity_and_protected_core():
    assert 'APP_VERSION = "v381"' in MAIN
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v381-transition-evidence-bridge"' in MAIN
    assert f'EXPECTED_CORE_BLOB_SHA = "{EXPECTED_CORE_BLOB_SHA}"' in MAIN
    assert CORE_PATH.exists()
    assert _git_blob_sha256(CORE_PATH.read_bytes()) == EXPECTED_CORE_BLOB_SHA


def test_v381_open_transition_never_delegates_to_legacy_generation_when_fit_is_absent():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v381_finalize")
    source = ast.get_source_segment(MAIN, fn)
    assert "if not aligned:" in source
    assert "return _original_generate_llm_response(*args, **kwargs)" not in source.split("if is_open_transition:", 1)[1]
    assert "_frame_neutral_evidence_unavailable_response" in source


def test_v381_open_transition_generation_context_is_transition_fit_only():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v381_finalize")
    source = ast.get_source_segment(MAIN, fn)
    assert "calibrated_docs = sorted(aligned" in source
    assert "calibrated_context = _rebuild_context_blocks(calibrated_docs)" in source
    assert "_call_original_with_calibrated_context" in source


def test_v381_source_compiles():
    ast.parse(MAIN)
