"""Tests for bounded, asynchronous fuzzy shadow observation."""
import json
import logging
import queue
import time

from guide_fuzzy_shadow_observer import record_shadow_comparison
import guide_fuzzy_shadow_observer as observer


def test_observer_logs_comparison_without_raw_query_or_url(caplog):
    query = "A private visitor question about repairing harm"
    url = "https://geralddaquila.com/canonical-resource/"
    candidates = [
        {"title": "Direct", "url": url, "_fuzzy_relevance_shadow": {"overall_shadow_score": 0.8, "harm_repair": 0.5}},
        {"title": "Adjacent", "url": "https://geralddaquila.com/adjacent/", "_fuzzy_relevance_shadow": {"overall_shadow_score": 0.3}},
    ]
    with caplog.at_level(logging.INFO, logger="guide.fuzzy_relevance.shadow"):
        record_shadow_comparison(query=query, candidates=candidates, selected=candidates[0])
        deadline = time.monotonic() + 2
        while not any("guide_fuzzy_relevance_shadow" in record.message for record in caplog.records) and time.monotonic() < deadline:
            time.sleep(0.01)
    matching = [record for record in caplog.records if "guide_fuzzy_relevance_shadow" in record.message]
    assert len(matching) == 1
    record = json.loads(matching[0].message)
    assert record["event"] == "guide_fuzzy_relevance_shadow"
    assert record["candidate_count"] == 2
    assert record["selected_matches_fuzzy_max"] is True
    assert query not in caplog.text
    assert url not in caplog.text
    assert "resource_id" in record["candidates"][0]


def test_observer_is_safe_with_missing_scores():
    record_shadow_comparison(query="question", candidates=[{"title": "No score", "url": "https://example.com"}], selected={})


def test_observer_drops_when_queue_is_full_without_raising(monkeypatch):
    def full(_record):
        raise queue.Full

    monkeypatch.setattr(observer, "_ensure_worker", lambda: None)
    monkeypatch.setattr(observer._QUEUE, "put_nowait", full)
    record_shadow_comparison(
        query="question",
        candidates=[{"title": "Direct", "url": "https://example.com", "_fuzzy_relevance_shadow": {"overall_shadow_score": 0.5}}],
        selected={"url": "https://example.com"},
    )


def test_logger_failure_is_isolated_from_worker():
    observer._emit_record({"event": "test"})
