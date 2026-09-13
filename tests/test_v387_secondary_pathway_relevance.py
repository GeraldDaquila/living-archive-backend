from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
CORE = ROOT / "use_core.py"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def test_v387_identity_and_core_integrity():
    assert 'APP_VERSION = "v387"' in MAIN
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v387-secondary-pathway-relevance"' in MAIN
    assert _git_blob_sha(CORE.read_bytes()) == EXPECTED_CORE_BLOB_SHA


def test_v387_source_compiles():
    ast.parse(MAIN)


def test_v387_acute_risk_resource_filter_is_present():
    assert "def _is_acute_risk_resource(doc: dict) -> bool:" in MAIN
    assert "and not profile.get(\"explicit_framework\") and not profile.get(\"risk\")" in MAIN
    assert "_is_acute_risk_resource(doc)" in MAIN


def test_v387_excludes_acute_risk_by_identity_not_only_query_overlap():
    assert "suicid(?:e|al|ality)" in MAIN
    assert "self-harm" in MAIN
    assert "crisis intervention" in MAIN
    assert "immediate danger" in MAIN


def test_v387_preserves_v386_core_or_transition_identity():
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
    assert "def _transition_profile(user_query: str) -> dict:" in MAIN
    assert "def _direct_open_transition_response(query: str, docs: list) -> dict:" in MAIN


def test_v387_secondary_roles_remain_structural():
    assert "def _secondary_role(doc: dict, profile: dict) -> str:" in MAIN
    assert "def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:" in MAIN
    assert "def _archive_bridge(profile: dict, meta: dict, secondaries: list) -> str:" in MAIN


def test_v387_keeps_production_visitor_boundary():
    assert "Where the material turns toward spiritual or afterlife possibilities" in MAIN
    assert "real-world safety and trusted human support" in MAIN
    assert "Take what feels useful, leave what does not" in MAIN
