from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_relational_refinement_is_structural():
    assert "def _evidence_boundary_note" in MAIN
    assert "def _secondary_role" in MAIN
    assert "def _guide_answer_architecture" in MAIN


def test_grief_bridge_uses_relational_voice():
    assert "This piece can be a gentle companion" in MAIN
    assert "What makes this one especially worthwhile" not in MAIN


def test_reflection_gateway_keeps_risk_filter_and_role_diversity():
    assert "if role in used_roles" in MAIN
    assert "profile.get(\"sensitive\") and not profile.get(\"risk\")" in MAIN


def test_runtime_seam_and_core_lock_remain_present():
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
    assert "app = use_core.app" in MAIN
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in MAIN
