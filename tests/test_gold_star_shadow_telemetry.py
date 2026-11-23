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


def test_structural_signature_matching_recognizes_inflected_reasoning_terms(monkeypatch):
    fixture = [{
        "id": "orientation-lesson",
        "query": "How can someone recover orientation during uncertainty?",
        "known_theme": "orientation, uncertainty, provisional agency",
        "assertions": ["Restore bearings without manufacturing certainty."],
        "runtime_transfer": True,
        "reasoning_family": "bounded_orientation_under_uncertainty",
        "qualifying_context": "ambiguity and transition while taking responsible action",
        "transferable_discipline": "Give bounded practical orientation without false certainty.",
        "abstention_boundary": "Do not manufacture certainty.",
        "variants": ["How do I regain my bearings amid uncertain change?"],
    }]
    monkeypatch.setattr(lessons, "_LESSONS", fixture)
    selected = lessons.select_lesson("How can I orient myself while things remain uncertain and unresolved?")
    assert selected is not None
    assert selected["benchmark_id"] == "orientation-lesson"
    assert selected["exact"] is False


def test_structural_signature_still_abstains_on_unrelated_topic(monkeypatch):
    fixture = [{
        "id": "orientation-lesson",
        "query": "How can someone recover orientation during uncertainty?",
        "known_theme": "orientation, uncertainty, provisional agency",
        "assertions": [],
        "runtime_transfer": True,
        "reasoning_family": "bounded_orientation_under_uncertainty",
        "qualifying_context": "ambiguity and transition",
        "transferable_discipline": "Give bounded practical orientation.",
        "abstention_boundary": "Do not manufacture certainty.",
        "variants": [],
    }]
    monkeypatch.setattr(lessons, "_LESSONS", fixture)
    assert lessons.select_lesson("What is the boiling point of water at sea level?") is None

def test_shadow_match_includes_opaque_request_correlation(monkeypatch, capsys):
    monkeypatch.setattr(lessons, "select_lesson", lambda q: {
        "benchmark_id": "approved-lesson-2", "score": 0.81, "exact": False
    })
    benchmark_id, score = lessons.shadow_observation(
        "private visitor wording",
        request_id="0123456789abcdef0123456789abcdef",
        request_ledger_version="2",
    )
    out = capsys.readouterr().out
    assert benchmark_id == "approved-lesson-2"
    assert score == 0.81
    assert "request_id=0123456789abcdef0123456789abcdef" in out
    assert "request_ledger_version=2" in out
    assert "private visitor wording" not in out


def test_shadow_observation_rejects_malformed_request_correlation(monkeypatch, capsys):
    monkeypatch.setattr(lessons, "select_lesson", lambda q: None)
    lessons.shadow_observation(
        "private visitor wording",
        request_id="not-a-request-token",
        request_ledger_version="2",
    )
    out = capsys.readouterr().out
    assert out.strip() == "gold_star_shadow match=abstain"
