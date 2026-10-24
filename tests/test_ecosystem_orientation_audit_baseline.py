from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "docs" / "qa" / "ECOSYSTEM_ORIENTATION_AUDIT_BASELINE.md"
STANDARD_PATH = ROOT / "docs" / "qa" / "SYSTEM_WIDE_ORIENTATION_AND_STRUCTURAL_FIX_STANDARD.md"


def test_ecosystem_audit_is_explicitly_a_baseline_not_live_certification():
    audit = AUDIT_PATH.read_text(encoding="utf-8")
    assert "Initial repository-level desk audit" in audit
    assert "do not establish that every visitor-facing route works correctly in production today" in audit
    assert "real browser" in audit.lower()


def test_ecosystem_audit_covers_priority_risks_and_exit_criteria():
    audit = AUDIT_PATH.read_text(encoding="utf-8")
    for required in (
        "P0",
        "P1",
        "P2",
        "source relevance",
        "primary/mirror",
        "Gold Standard status",
        "privacy-reviewed orientation measurement",
        "Exit criteria for the initial audit",
    ):
        assert required.lower() in audit.lower()


def test_ecosystem_audit_links_to_adopted_standard():
    audit = AUDIT_PATH.read_text(encoding="utf-8")
    standard = STANDARD_PATH.read_text(encoding="utf-8")
    assert "SYSTEM_WIDE_ORIENTATION_AND_STRUCTURAL_FIX_STANDARD.md" in audit
    assert "Every interaction should help a visitor move" in standard
