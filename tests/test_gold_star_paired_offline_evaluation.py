from scripts.gold_star_paired_offline_evaluation import evaluate_dataset

def test_paired_evaluation_reports_both_paths_without_certifying():
    answer = "Use os.getenv('TOKEN') is not None as a presence check. This does not prove the application reads it at runtime."
    report = evaluate_dataset({"cases": [{
        "case_id": "technical-1",
        "query": "How can I verify an environment variable is configured without exposing its secret value?",
        "llm": {"ok": True, "response": answer, "response_provenance": {"class": "llm"}},
        "deterministic": {"ok": True, "response": answer, "response_provenance": {"class": "deterministic_fallback"}},
    }]})
    assert report["paired_cases"] == 1
    assert report["status_parity"] == 1
    assert report["semantic_certification"] is False
    assert report["coverage"]["llm"]["review_required"] == 1
    assert report["coverage"]["deterministic"]["review_required"] == 1

def test_unsupported_path_is_reported_not_silently_dropped():
    report = evaluate_dataset({"cases": [{
        "case_id": "fact-1",
        "query": "What is the boiling point of water?",
        "llm": {"ok": True, "response": "100°C."},
        "deterministic": None,
    }]})
    assert report["paired_cases"] == 0
    assert report["coverage"]["deterministic"]["not_applicable"] == 1
    assert report["results"][0]["paths"]["deterministic"]["reason"] == "no_supported_fixture"
