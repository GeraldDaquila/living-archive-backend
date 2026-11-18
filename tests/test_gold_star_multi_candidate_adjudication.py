import inspect

import gold_star_lessons as lessons
import general_guide_composition as composition


def _candidate(benchmark_id, signature, family, discipline):
    return {
        "id": benchmark_id,
        "query": f"How should a steward reason about {signature}?",
        "known_theme": signature,
        "assertions": [],
        "runtime_transfer": True,
        "deterministic_fallback_eligible": False,
        "reasoning_family": family,
        "transferable_discipline": discipline,
        "abstention_boundary": f"Do not overextend {family}.",
        "variants": [],
        "signature_terms": set(signature.split()),
        "variant_terms": set(),
        "reasoning_terms": set(family.split()),
    }


def test_ranked_selector_returns_distinct_candidates_without_selecting_or_combining_them(monkeypatch):
    monkeypatch.setattr(lessons, "_LESSONS", [
        _candidate("one", "governance evidence comparison", "comparison", "compare evidence"),
        _candidate("two", "governance evidence accountability", "accountability", "trace responsibility"),
        _candidate("three", "governance evidence uncertainty", "uncertainty", "calibrate uncertainty"),
    ])
    result = lessons.select_lesson_candidates(
        "How should governance evidence guide accountability under uncertainty?",
        limit=3,
    )
    assert len(result) == 3
    assert len({item["benchmark_id"] for item in result}) == 3
    assert all(item["exact"] is False for item in result)
    assert all(item["score"] < 1.0 for item in result)
    # A ranked candidate list is deliberately not a verdict to combine all three.


def test_exact_match_remains_exclusive_and_dominates_approximate_candidates(monkeypatch):
    exact = _candidate("exact", "governance evidence comparison", "comparison", "compare evidence")
    near = _candidate("near", "governance evidence accountability", "accountability", "trace responsibility")
    exact["query"] = "How should governance evidence guide accountability under uncertainty?"
    monkeypatch.setattr(lessons, "_LESSONS", [near, exact])
    result = lessons.select_lesson_candidates(
        exact["query"] + "  ", limit=3
    )
    assert len(result) == 1
    assert result[0]["benchmark_id"] == "exact"
    assert result[0]["exact"] is True


def test_active_quality_contribution_exposes_candidate_comparison_fields_only(monkeypatch):
    candidates = [
        {
            "benchmark_id": f"candidate-{i}", "score": 0.71 - i * 0.02,
            "exact": False, "query": f"question {i}", "known_theme": f"theme {i}",
            "reasoning_family": f"family {i}", "transferable_discipline": f"discipline {i}",
            "abstention_boundary": f"boundary {i}",
        }
        for i in range(1, 4)
    ]
    monkeypatch.setattr(lessons, "select_lesson_candidates", lambda *args, **kwargs: candidates)
    result = lessons.active_quality_contribution("a question with three plausible candidates")
    assert len(result["candidates"]) == 3
    assert [x["benchmark_id"] for x in result["candidates"]] == [
        "candidate-1", "candidate-2", "candidate-3"
    ]
    assert result["authority_mode"] == "structural_guidance_only"
    assert all("expected_response" not in x and "doorway" not in x for x in result["candidates"])


def test_composition_contract_requires_select_combine_or_reject_adjudication():
    source = inspect.getsource(composition.compose)
    required = (
        "GOLD STAR MULTI-CANDIDATE ADJUDICATION",
        "Select one ",
        "only when it is the single sufficient fit.",
        "Combine candidates only when each contributes a distinct, ",
        "Reject all when none materially improves the answer or relevance is merely lexical.",
        "normally without Gold Star guidance",
        "not approved selections",
    )
    for phrase in required:
        assert phrase in source



def test_gold_star_adjudication_question_has_provider_independent_three_paragraph_answer(monkeypatch):
    query = (
        "A question has moderate similarity to three Gold Stars, each addressing a different "
        "reasoning discipline. How should USE decide whether to select one, combine several, "
        "or reject all three?"
    )
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda question: None)
    monkeypatch.setattr(composition, "_registered_exact_gold_standard", lambda question: None)

    def provider_must_not_run(**kwargs):
        raise AssertionError("The bounded adjudication answer must not depend on a provider.")

    monkeypatch.setattr(composition, "route_with_model_bank", provider_must_not_run)
    result = composition.compose(
        use_core=object(),
        query=query,
        context_data={},
    )

    assert result["provider"] == "bounded_gold_star_candidate_adjudication_recovery"
    assert result["doorway_title"] == ""
    assert result["doorway_url"] == ""
    paragraphs = [p for p in result["response"].split("\\n\\n") if p.strip()]
    assert len(paragraphs) == 3
    assert "similarity" in result["response"]
    assert "Select one" in result["response"]
    assert "Combine candidates only" in result["response"]
    assert "Reject all" in result["response"]
    assert "must not stop USE from answering" in result["response"]


def test_gold_star_adjudication_recovery_does_not_capture_unrelated_questions():
    assert composition._gold_star_candidate_adjudication_recovery(
        "How should I choose between three leadership approaches?"
    ) is None
