"""Tests for privacy-conscious, failure-isolated fuzzy shadow observation."""
import json
import logging

from guide_fuzzy_shadow_observer import record_shadow_comparison


def test_observer_logs_comparison_without_raw_query_or_url(caplog):
    query = "A private visitor question about repairing harm"
    url = "https://geralddaquila.com/canonical-resource/"
    candidates = [
        {"title": "Direct", "url": url, "_fuzzy_relevance_shadow": {"overall_shadow_score": 0.8, "harm_repair": 0.5}},
        {"title": "Adjacent", "url": "https://geralddaquila.com/adjacent/", "_fuzzy_relevance_shadow": {"overall_shadow_score": 0.3}},
    ]
    with caplog.at_level(logging.INFO, logger="guide.fuzzy_relevance.shadow"):
        record_shadow_comparison(query=query, candidates=candidates, selected=candidates[0])
    assert len(caplog.records) == 1
    record = json.loads(caplog.records[0].message)
    assert record["event"] == "guide_fuzzy_relevance_shadow"
    assert record["candidate_count"] == 2
    assert record["selected_matches_fuzzy_max"] is True
    assert query not in caplog.text
    assert url not in caplog.text
    assert "resource_id" in record["candidates"][0]


def test_observer_is_safe_with_missing_scores():
    record_shadow_comparison(query="question", candidates=[{"title": "No score", "url": "https://example.com"}], selected={})


def test_observer_never_raises_when_logger_fails(monkeypatch):
    import guide_fuzzy_shadow_observer as observer

    def broken(*args, **kwargs):
        raise RuntimeError("logging unavailable")

    monkeypatch.setattr(observer._LOGGER, "info", broken)
    record_shadow_comparison(
        query="question",
        candidates=[{"title": "Direct", "url": "https://example.com", "_fuzzy_relevance_shadow": {"overall_shadow_score": 0.5}}],
        selected={"url": "https://example.com"},
    )
