from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_runtime_seam_is_present():
    assert "app = use_core.app" in MAIN
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in MAIN


def test_recommendation_context_fallbacks_are_present():
    assert "retrieved_context_blocks" in MAIN
    assert "canonical_link_context" in MAIN
    assert "_context_blocks_from_kwargs(args, kwargs)" in MAIN


def test_risk_aware_selection_preserves_general_recommendations():
    assert "if profile.get(\"sensitive\") and not profile.get(\"risk\")" in MAIN
    assert "suicid" in MAIN
    assert "self-harm" in MAIN
