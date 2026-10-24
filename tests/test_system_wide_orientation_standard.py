from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STANDARD_PATH = ROOT / "docs" / "qa" / "SYSTEM_WIDE_ORIENTATION_AND_STRUCTURAL_FIX_STANDARD.md"
REGISTRY_GUIDE_PATH = ROOT / "docs" / "qa" / "GOLD_STANDARD_REGISTRY.md"


def test_system_wide_structural_fix_standard_covers_all_navigation_specialists():
    standard = STANDARD_PATH.read_text(encoding="utf-8")
    for specialist in (
        "The Guide / USE",
        "Living Glossary",
        "Catalogue",
        "Atlas",
        "Glyph Finder",
        "Human Relational Navigator (HRN)",
        "Fractal Systems Diagnostic (FSD)",
    ):
        assert specialist in standard


def test_structural_fix_standard_requires_root_cause_neighbors_and_live_boundary():
    standard = STANDARD_PATH.read_text(encoding="utf-8")
    for required in (
        "Observed failure",
        "Intended behavior",
        "Root cause",
        "Correct layer",
        "Invariants and protected boundaries",
        "Regression matrix",
        "Evidence of success",
        "Closure status",
        "neighboring case",
        "real browser E2E",
        "does not prove the WordPress visitor interface works",
    ):
        assert required.lower() in standard.lower()


def test_structural_fix_standard_separates_provenance_and_orientation_measurement():
    standard = STANDARD_PATH.read_text(encoding="utf-8")
    for required in (
        "established general knowledge",
        "direct canonical Archive evidence",
        "system-generated interpretation",
        "Traffic and clicks are activity metrics, not proof of orientation",
        "data minimization",
        "Do not upgrade a case to Gold Standard solely because it passes an automated test",
    ):
        assert required in standard


def test_gold_standard_registry_links_to_system_wide_standard():
    registry_guide = REGISTRY_GUIDE_PATH.read_text(encoding="utf-8")
    assert "SYSTEM_WIDE_ORIENTATION_AND_STRUCTURAL_FIX_STANDARD.md" in registry_guide
