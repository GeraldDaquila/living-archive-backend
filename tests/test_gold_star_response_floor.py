"""Cross-source acceptance tests for the Gold Star v2.0 shared response floor."""
from gold_star_response_floor import evaluate_response_floor


def test_same_floor_applies_to_llm_gold_star_and_deterministic_sources():
    sources = ("llm", "exact_gold_star", "deterministic_fallback", "specialist")
    for source in sources:
        result = evaluate_response_floor(
            "What is photosynthesis?",
            {"ok": True, "query": "What is photosynthesis?",
             "response": "Photosynthesis converts light energy into chemical energy.",
             "response_provenance": {"class": source}},
            exact_standard=(source == "exact_gold_star"),
        )
        assert result["status"] == "pass"
        assert result["source_independent"] is True
        assert result["exact_standard_immutable"] is (source == "exact_gold_star")


def test_floor_rejects_missing_or_generic_answers_for_every_source():
    for source in ("llm", "exact_gold_star", "deterministic_fallback", "specialist"):
        missing = evaluate_response_floor(
            "Explain the issue.", {"ok": True, "query": "Explain the issue.",
            "response_provenance": {"class": source}},
            exact_standard=(source == "exact_gold_star"),
        )
        generic = evaluate_response_floor(
            "Explain the issue.", {"ok": True, "query": "Explain the issue.",
            "response": "I cannot answer that question.",
            "response_provenance": {"class": source}},
            exact_standard=(source == "exact_gold_star"),
        )
        assert missing["status"] == "fail"
        assert generic["status"] == "fail"


def test_floor_does_not_rewrite_frozen_gold_star_content():
    frozen = "Photosynthesis converts light energy into chemical energy."
    payload = {"ok": True, "query": "What is photosynthesis?", "response": frozen}
    result = evaluate_response_floor(
        payload["query"], payload, exact_standard=True
    )
    assert result["status"] == "pass"
    assert payload["response"] == frozen


def test_error_payloads_are_not_misclassified_as_successful_answers():
    result = evaluate_response_floor(
        "Explain the issue.", {"ok": False, "response": ""}
    )
    assert result["status"] == "not_applicable"
    assert result["reason"] == "explicit_error_payload"


def test_markup_and_missing_query_context_fail_closed():
    assert evaluate_response_floor(
        "Question?", {"ok": True, "query": "Question?",
                      "response": "<script>alert(1)</script>"}
    )["status"] == "fail"
    assert evaluate_response_floor(
        "", {"ok": True, "response": "A complete answer."}
    )["status"] == "fail"


def test_structured_specialist_handoff_uses_its_own_contract():
    result = evaluate_response_floor(
        "I need help entering the Stewardship Institute.",
        {"ok": True, "query": "I need help entering the Stewardship Institute.",
         "handoff": "formation_entrance", "handoff_pending": True, "response": ""},
    )
    assert result["status"] == "not_applicable"
    assert result["reason"] == "structured_handoff"
