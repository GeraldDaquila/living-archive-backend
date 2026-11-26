from pathlib import Path


def test_observation_only_gold_star_semantic_retrieval_is_not_on_basic_inquiry_path():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_response(")
    window = source[start:start + 1200]
    assert "_gold_star_shadow_observation(" not in window
    assert "_gold_star_shadow_observation(" not in source
    # The request budget begins immediately; diagnostic-only semantic retrieval
    # must not run before it or consume the visitor's latency/memory budget.
    assert window.index("started = time.perf_counter()") < window.index(
        "request_deadline = time.monotonic()"
    )


def test_gold_star_active_quality_contribution_remains_wired_into_composition():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert "_gold_star_active_quality_contribution(question)" in source
    assert "GOLD STAR MULTI-CANDIDATE ADJUDICATION" in source
    assert "Select the smallest sufficient set; prefer one specific candidate when it covers the task." in source
    assert "Combine only when each adds a distinct, necessary, compatible operation not already covered." in source
    assert "Reject all when none improves the answer" in source
