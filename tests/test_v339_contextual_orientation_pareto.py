from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_contextual_orientation_instruments_exist():
    assert "def _secondary_path_context" in MAIN
    assert "_secondary_path_context(doc, profile)" in MAIN
    assert "a broader exploration of what different traditions and experiences have made of life after death" in MAIN


def test_existing_guide_architecture_is_preserved():
    assert "def _query_profile(user_query: str, docs: list) -> dict:" in MAIN
    assert "def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:" in MAIN
    assert "def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:" in MAIN
    assert "This piece can be a gentle companion" in MAIN
    assert "profile.get(\"sensitive\") and not profile.get(\"risk\")" in MAIN


def test_runtime_and_core_integrity_are_preserved():
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
    assert "app = use_core.app" in MAIN
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in MAIN
