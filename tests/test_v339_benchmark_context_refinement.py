from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_contextual_reflection_gateway_instrumentation_exists():
    assert "def _secondary_role" in MAIN
    assert "def _select_secondary_pathways" in MAIN
    assert "def _guide_answer_architecture" in MAIN


def test_relational_guide_voice_is_preserved():
    assert "This piece can be a gentle companion" in MAIN
    assert "a way to explore" in MAIN


def test_risk_aware_gateway_is_preserved():
    assert "profile.get(\"sensitive\") and not profile.get(\"risk\")" in MAIN
    assert "suicid" in MAIN
    assert "self-harm" in MAIN


def test_runtime_and_core_integrity_markers_are_preserved():
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
    assert "app = use_core.app" in MAIN
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in MAIN
