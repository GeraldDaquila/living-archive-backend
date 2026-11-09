import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_manifest():
    return json.loads((ROOT / "archive_crosslink_editorial_manifest.json").read_text())


def test_manifest_preserves_two_verified_candidate_omissions():
    manifest = load_manifest()
    assert set(manifest["include_wp_ids"]) == {"76640", "80702"}


def test_manifest_makes_duplicate_exclusions_explicit():
    manifest = load_manifest()
    excluded = manifest["exclude_wp_ids"]
    assert len([key for key, value in excluded.items() if value.startswith("numeric duplicate")]) == 34
    assert excluded["6357"].startswith("legacy URL")


def test_unresolved_records_are_not_silently_classified():
    manifest = load_manifest()
    assert set(manifest["review_required_wp_ids"]) == {"75221", "7390"}
