import gold_star_lessons as lessons

def test_shadow_match_emits_metadata_without_query_or_answer_content(monkeypatch, capsys):
    monkeypatch.setattr(lessons, "select_lesson", lambda q: {
        "benchmark_id": "approved-lesson-1", "score": 0.73, "exact": False
    })
    benchmark_id, score = lessons.shadow_observation("private visitor wording should never be logged")
    out = capsys.readouterr().out
    assert benchmark_id == "approved-lesson-1"
    assert score == 0.73
    assert "match=matched" in out
    assert "benchmark_id=approved-lesson-1" in out
    assert "score=0.730" in out
    assert "kind=cross_question" in out
    assert "private visitor wording" not in out

def test_shadow_abstention_emits_explicit_event(monkeypatch, capsys):
    monkeypatch.setattr(lessons, "select_lesson", lambda q: None)
    assert lessons.shadow_observation("another private visitor question") == (None, None)
    out = capsys.readouterr().out
    assert out.strip() == "gold_star_shadow match=abstain"
