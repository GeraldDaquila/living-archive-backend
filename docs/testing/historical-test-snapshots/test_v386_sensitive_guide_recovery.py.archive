from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
CORE = ROOT / "use_core.py"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def test_v386_identity_and_core_integrity():
    assert 'APP_VERSION = "v386"' in MAIN
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v386-proven-guide-bridge-on-v385"' in MAIN
    assert f'EXPECTED_CORE_BLOB_SHA = "{EXPECTED_CORE_BLOB_SHA}"' in MAIN
    assert _git_blob_sha(CORE.read_bytes()) == EXPECTED_CORE_BLOB_SHA


def test_v386_source_compiles():
    ast.parse(MAIN)


def test_v386_uses_adjudicated_primary_and_no_benchmark_fallback():
    assert "use_core._adjudicate_recommendation_resource(docs,user_query)" in MAIN
    assert "_BENCHMARK_PRIMARY_TITLE" not in MAIN
    assert "_BENCHMARK_PRIMARY_URL" not in MAIN


def test_v386_preserves_v385_transition_branch():
    tree = ast.parse(MAIN)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v386_finalize")
    source = ast.get_source_segment(MAIN, fn)
    branch = source.split('if tprofile["transition"]', 1)[1].split('profile=_query_profile', 1)[0]
    assert "_transition_retrieval_strategy" in branch
    assert "return _direct_open_transition_response" in branch
    assert "_original_generate_llm_response" not in branch


def test_v386_archive_bridge_is_structural_and_reusable():
    assert "def _archive_bridge(profile: dict, meta: dict, secondaries: list) -> str:" in MAIN
    assert "def _extract_archive_metadata(doc: dict, docs: list) -> dict:" in MAIN
    assert "def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:" in MAIN
    assert "def _build_sensitive_recommendation_answer(user_query: str, primary: dict, docs: list) -> str:" in MAIN


def test_v386_renders_epistemic_boundary_and_risk_route():
    assert "those are perspectives offered by the work rather than established facts" in MAIN
    assert "real-world safety and trusted human support" in MAIN
    assert "Take what feels useful, leave what does not" in MAIN
