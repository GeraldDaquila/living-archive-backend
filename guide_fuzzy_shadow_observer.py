"""Privacy-conscious, bounded, asynchronous telemetry for fuzzy shadow scoring.

The request path only builds a bounded record and attempts a non-blocking queue
insert. A daemon worker emits records. A full queue drops diagnostics rather
than applying back-pressure to visitor requests. No durable storage is implied.
"""
import hashlib
import json
import logging
import queue
import threading

_LOGGER = logging.getLogger("guide.fuzzy_relevance.shadow")
_QUEUE = queue.Queue(maxsize=512)
_WORKER_LOCK = threading.Lock()
_WORKER_STARTED = False


def _digest(value):
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def _emit_record(record):
    """Worker-only logger seam; never called directly by the request path."""
    try:
        _LOGGER.info("%s", json.dumps(record, sort_keys=True, separators=(",", ":")))
    except Exception:
        return


def _worker():
    while True:
        record = _QUEUE.get()
        try:
            _emit_record(record)
        finally:
            _QUEUE.task_done()


def _ensure_worker():
    global _WORKER_STARTED
    if _WORKER_STARTED:
        return
    with _WORKER_LOCK:
        if _WORKER_STARTED:
            return
        thread = threading.Thread(
            target=_worker,
            name="guide-fuzzy-shadow-telemetry",
            daemon=True,
        )
        thread.start()
        _WORKER_STARTED = True


def record_shadow_comparison(*, query, candidates, selected):
    """Queue bounded diagnostics without raw visitor text or canonical URLs."""
    try:
        unique = {}
        for candidate in candidates or []:
            if not isinstance(candidate, dict):
                continue
            score = candidate.get("_fuzzy_relevance_shadow")
            if not isinstance(score, dict):
                continue
            url = str(candidate.get("url") or candidate.get("canonical_url") or "").strip()
            title = str(candidate.get("title") or "").strip()
            if not url or not title:
                continue
            key = _digest(url)
            unique[key] = {
                "resource_id": key,
                "score": {
                    str(name)[:48]: round(float(value), 4)
                    for name, value in score.items()
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                },
            }
        if not unique:
            return
        selected_url = str((selected or {}).get("url") or (selected or {}).get("canonical_url") or "").strip()
        selected_id = _digest(selected_url) if selected_url else None
        scored = [
            item["score"].get("overall_shadow_score", 0.0)
            for item in unique.values()
        ]
        max_score = max(scored, default=None)
        selected_score = unique.get(selected_id, {}).get("score", {}).get("overall_shadow_score")
        record = {
            "event": "guide_fuzzy_relevance_shadow",
            "query_id": _digest(query),
            "candidate_count": len(unique),
            "selected_resource_id": selected_id,
            "selected_score": selected_score,
            "max_candidate_score": max_score,
            "selected_matches_fuzzy_max": (
                selected_score is not None and max_score is not None and selected_score == max_score
            ),
            "candidates": list(unique.values())[:30],
        }
        _ensure_worker()
        _QUEUE.put_nowait(record)
    except (queue.Full, Exception):
        # Never back-pressure or fail the visitor request for shadow diagnostics.
        return
