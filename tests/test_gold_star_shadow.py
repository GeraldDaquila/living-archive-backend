from gold_star_shadow import evaluate_gold_star_shadow


def test_shadow_mode_records_abstention_without_answer_content():
    event = evaluate_gold_star_shadow("How do I calculate the area of a triangle?")
    assert event["gold_star_shadow"] is True
    assert event["selected"] is False
    assert "answer" not in event


def test_shadow_mode_records_selected_benchmark_only():
    event = evaluate_gold_star_shadow("What is institutional memory, and why does it matter?")
    assert event["gold_star_shadow"] is True
    assert event["selected"] is True
    assert event["benchmark_id"]
    assert event["score"] > 0
    assert "answer" not in event
