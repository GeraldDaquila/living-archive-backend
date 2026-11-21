from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
CORE = ROOT / "use_core.py"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def test_v383_identity_and_core_integrity():
    assert 'APP_VERSION = "v383"' in MAIN
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v383-direct-open-transition-bridge"' in MAIN
    assert f'EXPECTED_CORE_BLOB_SHA = "{EXPECTED_CORE_BLOB_SHA}"' in MAIN
    assert _git_blob_sha(CORE.read_bytes()) == EXPECTED_CORE_BLOB_SHA


def test_v383_open_transition_uses_only_transition_fit_context():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v383_finalize")
    source = ast.get_source_segment(MAIN, fn)
    branch = source.split("if is_open_transition:", 1)[1].split("if profile.get(\"explicit_framework\")", 1)[0]
    assert "existing_aligned" in branch
    assert "_transition_retrieval_strategy" in branch
    assert "calibrated_context = _rebuild_context_blocks(calibrated_docs)" in branch
    assert "_call_original_with_calibrated_context" in branch
    assert "raw_context" not in branch.split("return _call_original_with_calibrated_context", 1)[0]


def test_v383_source_compiles():
    ast.parse(MAIN)
