from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_final_benchmark_polish_preserves_structure_and_provenance():
    assert "def _archive_constellation_interpretation(meta: dict, profile: dict) -> str:" in MAIN
    assert "def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:" in MAIN
    assert "def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:" in MAIN
    assert "This piece can be a gentle companion" in MAIN
    assert "profile.get(\"sensitive\") and not profile.get(\"risk\")" in MAIN
    assert "_secondary_path_context(doc, profile)" in MAIN
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in MAIN


def test_final_interpretation_is_generic_not_benchmark_literal():
    assert "Together, those neighboring pieces" in MAIN
    assert "profile.get(\"meaning\") and profile.get(\"sensitive\")" in MAIN
