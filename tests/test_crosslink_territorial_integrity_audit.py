import hashlib
import json

import pytest

from scripts.audit_archive_crosslink_integrity import (
    build_report,
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
    assert len(result["duplicate_normalized_titles_in_registry"]) == 2
    assert len(result["duplicate_normalized_titles_in_snapshot"]) == 1


def test_metadata_addressability_distinguishes_missing_search_fields():
    assets = [
        _asset(1, "Usable Title", "https://geralddaquila.com/a", resource_type="page"),
        _asset(2, "", "https://geralddaquila.com/b", resource_type="page"),
        _asset(3, "Title", "https://external.example/b", resource_type="page"),
        _asset(4, "Title", "https://geralddaquila.com/d", resource_type=""),
    ]
    result = metadata_addressability(assets)
    assert result["addressable_count"] == 2
    assert result["non_addressable_count"] == 2
    assert {x["wp_id"] for x in result["non_addressable_assets"]} == {"2", "3"}

class _FakeResponse:
    status = 200

    def __init__(self, url):
        self._url = url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _http_error(url, status, headers=None):
    from urllib.error import HTTPError

    return HTTPError(url, status, "synthetic response", headers or {}, None)


def test_destination_request_pacer_enforces_global_minimum_spacing(monkeypatch):
    from scripts import audit_archive_crosslink_integrity as audit

    clock = {"now": 100.0}
    sleeps = []
    monkeypatch.setattr(audit, "_LINK_NEXT_REQUEST_AT", 0.0)
    monkeypatch.setattr(audit.time, "monotonic", lambda: clock["now"])

    def fake_sleep(seconds):
        sleeps.append(seconds)
        clock["now"] += seconds

    monkeypatch.setattr(audit.time, "sleep", fake_sleep)

    audit._pace_link_request()
    audit._pace_link_request()

    assert sleeps == [pytest.approx(audit.LINK_DELAY_SECONDS)]
    assert clock["now"] == pytest.approx(100.0 + audit.LINK_DELAY_SECONDS)
    assert audit._LINK_NEXT_REQUEST_AT == pytest.approx(100.0 + 2 * audit.LINK_DELAY_SECONDS)


def test_destination_head_429_honors_retry_after_and_paces_each_attempt(monkeypatch):
    from scripts import audit_archive_crosslink_integrity as audit

    calls = []
    sleeps = []
    responses = [
        _http_error("https://geralddaquila.com/a", 429, {"Retry-After": "2"}),
        _FakeResponse("https://geralddaquila.com/a"),
    ]

    def fake_urlopen(request, timeout):
        calls.append(request.get_method())
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(audit, "_pace_link_request", lambda: calls.append("paced"))
    monkeypatch.setattr(audit, "urlopen", fake_urlopen)
    monkeypatch.setattr(audit.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = audit.check_destination(_asset(10, "A", "https://geralddaquila.com/a"))

    assert result["status"] == "ok"
    assert result["method"] == "HEAD"
    assert calls == ["paced", "HEAD", "paced", "HEAD"]
    assert sleeps == [2.0]


def test_destination_get_fallback_uses_same_429_retry_policy(monkeypatch):
    from scripts import audit_archive_crosslink_integrity as audit

    calls = []
    sleeps = []
    responses = [
        _http_error("https://geralddaquila.com/a", 405),
        _http_error("https://geralddaquila.com/a", 429, {"Retry-After": "3"}),
        _FakeResponse("https://geralddaquila.com/a"),
    ]

    def fake_urlopen(request, timeout):
        calls.append(request.get_method())
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(audit, "_pace_link_request", lambda: calls.append("paced"))
    monkeypatch.setattr(audit, "urlopen", fake_urlopen)
    monkeypatch.setattr(audit.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = audit.check_destination(_asset(11, "A", "https://geralddaquila.com/a"))

    assert result["status"] == "ok"
    assert result["method"] == "GET"
    assert calls == ["paced", "HEAD", "paced", "GET", "paced", "GET"]
    assert sleeps == [3.0]


def test_destination_429_retries_are_bounded_and_report_rate_limited(monkeypatch):
    from scripts import audit_archive_crosslink_integrity as audit

    calls = []
    sleeps = []

    def fake_urlopen(request, timeout):
        calls.append(request.get_method())
        raise _http_error(request.full_url, 429)

    monkeypatch.setattr(audit, "_pace_link_request", lambda: None)
    monkeypatch.setattr(audit, "urlopen", fake_urlopen)
    monkeypatch.setattr(audit.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = audit.check_destination(_asset(12, "A", "https://geralddaquila.com/a"))

    assert result["status"] == "rate_limited"
    assert result["http_status"] == 429
    assert len(calls) == audit.LINK_429_RETRIES + 1
    assert sleeps == [5.0, 10.0, 20.0]

def test_destination_retry_after_above_wait_budget_is_not_retried_early(monkeypatch):
    from scripts import audit_archive_crosslink_integrity as audit

    calls = []
    sleeps = []

    def fake_urlopen(request, timeout):
        calls.append(request.get_method())
        raise _http_error(request.full_url, 429, {"Retry-After": "120"})

    monkeypatch.setattr(audit, "_pace_link_request", lambda: None)
    monkeypatch.setattr(audit, "urlopen", fake_urlopen)
    monkeypatch.setattr(audit.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = audit.check_destination(_asset(13, "A", "https://geralddaquila.com/a"))

    assert result["status"] == "rate_limited"
    assert calls == ["HEAD"]
    assert sleeps == []


def test_rate_limits_and_network_errors_are_indeterminate_not_broken():
    snapshot = {
        "assets": [],
        "asset_count": 0,
        "refreshed_at": 0,
    }
    empty_registry = {
        "posts": {"records": [], "pages": [], "total_header": "0", "total_pages_header": "0"},
        "pages": {"records": [], "pages": [], "total_header": "0", "total_pages_header": "0"},
    }
    report = build_report(
        snapshot=snapshot,
        snapshot_sha="abc",
        snapshot_bytes=0,
        checksum_expected="abc",
        registry_data=empty_registry,
        link_results=[
            {"wp_id": "20", "url": "https://geralddaquila.com/a", "status": "rate_limited"},
            {"wp_id": "21", "url": "https://geralddaquila.com/b", "status": "network_error"},
        ],
        link_check_performed=True,
    )

    destination = report["destination_integrity"]
    assert destination["broken_count"] == 0
    assert destination["indeterminate_count"] == 2
    assert destination["rate_limited_count"] == 1
    assert destination["network_error_count"] == 1
    assert report["completeness_gates"]["no_broken_destinations"] is True
    assert report["completeness_gates"]["destination_results_determinate"] is False
    assert report["overall_status"] == "ATTENTION REQUIRED"

