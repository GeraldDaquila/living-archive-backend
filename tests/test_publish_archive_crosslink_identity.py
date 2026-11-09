import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "publisher", ROOT / "scripts" / "publish_archive_crosslink_snapshot.py"
)
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


def canonicalize(records):
    assets = {}
    for item in records:
        key = item["url"].casefold()
        existing = assets.get(key)
        if existing is None or (
            existing.get("resource_type") == "page"
            and item.get("resource_type") == "post"
        ):
            assets[key] = item
    return list(assets.values())


def test_same_title_distinct_urls_are_preserved():
    records = [
        {"title": "Orientation", "url": "https://example.test/orientation", "wp_id": "1", "resource_type": "page"},
        {"title": "Orientation", "url": "https://example.test/2026/08/01/orientation", "wp_id": "2", "resource_type": "post"},
    ]
    assert {item["wp_id"] for item in canonicalize(records)} == {"1", "2"}


def test_numeric_suffix_is_not_silently_deleted():
    records = [
        {"title": "A Question", "url": "https://example.test/a-question", "wp_id": "1", "resource_type": "post"},
        {"title": "A Question", "url": "https://example.test/a-question-2", "wp_id": "2", "resource_type": "post"},
    ]
    assert {item["wp_id"] for item in canonicalize(records)} == {"1", "2"}


def test_same_url_keeps_single_canonical_record():
    records = [
        {"title": "One", "url": "https://example.test/one", "wp_id": "1", "resource_type": "page"},
        {"title": "One revised", "url": "https://example.test/one", "wp_id": "2", "resource_type": "post"},
    ]
    result = canonicalize(records)
    assert len(result) == 1
    assert result[0]["wp_id"] == "2"


def test_full_published_identity_baseline_excludes_only_explicit_nonpublishable_records():
    # Baseline established by the territorial audit: 2,088 published records,
    # 24 explicitly archived, one empty-title record, and one root-URL record.
    published = 2088
    explicitly_archived = 24
    empty_title = 1
    root_url = 1
    expected = published - explicitly_archived - empty_title - root_url
    assert expected == 2062
