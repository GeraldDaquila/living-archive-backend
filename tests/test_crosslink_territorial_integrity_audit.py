import hashlib
import json

import pytest

from scripts.audit_archive_crosslink_integrity import (
    compare_registry,
    load_snapshot,
    metadata_addressability,
    normalize_url,
    title_key,
)


def _asset(wp_id, title, url, **extra):
    return {
        "wp_id": str(wp_id),
        "title": title,
        "url": url,
        "resource_type": "page",
        "summary": "",
        **extra,
    }


def _registry(wp_id, title, url, post_type="page"):
    return {
        "wp_id": str(wp_id),
        "title": title,
        "title_key": title_key(title),
        "url": normalize_url(url),
        "post_type": post_type,
    }


def test_normalize_url_accepts_only_site_https_and_normalizes_trailing_slash():
    assert normalize_url("https://geralddaquila.com/example/") == "https://geralddaquila.com/example"
    assert normalize_url("http://geralddaquila.com/example") == ""
    assert normalize_url("https://example.com/example") == ""


def test_title_key_decodes_entities_and_normalizes_markup():
    assert title_key("Living <em>Archive</em> &amp; Stewardship") == "living archive stewardship"


def test_snapshot_loader_requires_v2_wordpress_contract(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({
        "contract": "archive-crosslink-inventory-v2",
        "source": "wordpress-canonical-registry",
        "crosslink_ready": True,
        "complete": True,
        "assets": [],
    }), encoding="utf-8")
    snapshot, digest, size = load_snapshot(path)
    assert snapshot["contract"] == "archive-crosslink-inventory-v2"
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert size == path.stat().st_size

    path.write_text(json.dumps({
        "contract": "archive-crosslink-inventory-v1",
        "source": "pinecone",
        "crosslink_ready": True,
        "complete": True,
        "assets": [],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="Only archive-crosslink-inventory-v2"):
        load_snapshot(path)


def test_comparison_distinguishes_missing_stale_and_identity_mismatch():
    snapshot = [
        _asset(1, "One", "https://geralddaquila.com/one"),
        _asset(2, "Old Two", "https://geralddaquila.com/old-two"),
        _asset(4, "Four", "https://geralddaquila.com/four"),
    ]
    registry = [
        _registry(1, "One", "https://geralddaquila.com/one"),
        _registry(2, "New Two", "https://geralddaquila.com/new-two"),
        _registry(3, "Three", "https://geralddaquila.com/three"),
    ]
    result = compare_registry(snapshot, registry)
    assert result["missing_wp_ids"] == ["3"]
    assert result["stale_wp_ids"] == ["4"]
    assert [item["wp_id"] for item in result["identity_mismatches"]] == ["2"]


def test_comparison_reports_duplicate_ids_urls_and_titles_without_collapsing():
    snapshot = [
        _asset(10, "Duplicate Name", "https://geralddaquila.com/a"),
        _asset(11, "Duplicate Name", "https://geralddaquila.com/b"),
    ]
    registry = [
        _registry(10, "Duplicate Name", "https://geralddaquila.com/a"),
        _registry(11, "Duplicate Name", "https://geralddaquila.com/b"),
        _registry(12, "Another Title", "https://geralddaquila.com/a"),
        _registry(12, "Another Title", "https://geralddaquila.com/a"),
    ]
    result = compare_registry(snapshot, registry)
    assert len(result["duplicate_wp_ids_in_registry"]) == 1
    assert len(result["duplicate_canonical_urls_in_registry"]) == 1
    assert len(result["duplicate_normalized_titles_in_registry"]) == 1
    assert len(result["duplicate_normalized_titles_in_snapshot"]) == 1


def test_metadata_addressability_distinguishes_missing_search_fields():
    assets = [
        _asset(1, "Usable Title", "https://geralddaquila.com/a", resource_type="page"),
        _asset(2, "", "https://geralddaquila.com/b", resource_type="page"),
        _asset(3, "Title", "https://external.example/b", resource_type="page"),
        _asset(4, "Title", "https://geralddaquila.com/d", resource_type=""),
    ]
    result = metadata_addressability(assets)
    assert result["addressable_count"] == 1
    assert result["non_addressable_count"] == 3
    assert {x["wp_id"] for x in result["non_addressable_assets"]} == {"2", "3", "4"}
