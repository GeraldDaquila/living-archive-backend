from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
CORE = ROOT / "use_core.py"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

import hashlib

def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def test_v386_identity_and_protected_core():
    assert 'APP_VERSION = "v386"' in MAIN
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v386-browser-response-visibility"' in MAIN
    assert f'EXPECTED_CORE_BLOB_SHA = "{EXPECTED_CORE_BLOB_SHA}"' in MAIN
    assert _git_blob_sha(CORE.read_bytes()) == EXPECTED_CORE_BLOB_SHA


def test_v386_runtime_source_compiles():
    ast.parse(MAIN)


def test_v386_preserves_direct_open_transition_path():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v386_finalize")
    source = ast.get_source_segment(MAIN, fn)
    branch = source.split("if is_open_transition:", 1)[1].split("if profile.get(\"explicit_framework\")", 1)[0]
    assert "_transition_retrieval_strategy" in branch
    assert "return _direct_open_transition_response" in branch
    assert "_original_generate_llm_response" not in branch
