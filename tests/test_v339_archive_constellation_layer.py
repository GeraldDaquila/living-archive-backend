from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")


def test_archive_constellation_instrument_exists():
    assert "def _archive_context(doc: dict, docs: list) -> str:" in MAIN
    assert "archive_context = _archive_context(primary, docs)" in MAIN
    assert "architecture[\"archive_context\"]" in MAIN
    assert "sections.append(architecture[\"archive_context\"] + \".\")" in MAIN


def test_existing_gateway_architecture_is_preserved():
    assert "def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:" in MAIN
    assert "def _secondary_path_context(doc: dict, profile: dict) -> str:" in MAIN
    assert "This piece can be a gentle companion" in MAIN
    assert "profile.get(\"sensitive\") and not profile.get(\"risk\")" in MAIN


def test_runtime_and_core_integrity_are_preserved():
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in MAIN
    assert "app = use_core.app" in MAIN
    assert "use_core.generate_llm_response = _v339_finalize_generation_response" in MAIN
