from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_archive_interpretive_bridge_exists_and_is_the_structural_layer():
    assert "def _archive_constellation_interpretation(meta: dict, profile: dict) -> str:" in MAIN
    assert "def _archive_bridge(profile: dict, meta: dict, secondaries: list) -> str:" in MAIN
    assert "archive_interpretation = _archive_constellation_interpretation(archive_meta, profile)" in MAIN
    assert "archive_bridge = _archive_bridge(profile, archive_meta, secondaries)" in MAIN
    assert "architecture[\"archive_bridge\"]" in MAIN
    assert "sections.append(architecture[\"archive_bridge\"])" in MAIN
    assert "and architecture[\"archive_interpretation\"] != architecture[\"archive_bridge\"]" in MAIN


def test_existing_archive_and_gateway_instruments_are_preserved():
    assert "def _extract_archive_metadata(doc: dict, docs: list) -> dict:" in MAIN
    assert "def _archive_context(doc: dict, docs: list) -> str:" in MAIN
    assert "def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:" in MAIN
    assert "This piece can be a gentle companion" in MAIN
    assert "profile.get(\"sensitive\") and not profile.get(\"risk\")" in MAIN
    assert "_secondary_path_context(doc, profile)" in MAIN


def test_runtime_and_core_integrity_are_preserved():
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
    assert "app = use_core.app" in MAIN
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in MAIN
