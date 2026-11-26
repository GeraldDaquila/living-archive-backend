"""Request-level Gold Star eligibility disposition and privacy contract tests."""

import gold_star_adjudication_trace as ledger


def _classify(payload=None, *, status=200, completed=True, has_query=True, seam=False):
    return ledger.classify_request_disposition(
        payload=payload,
        status_code=status,
        response_completed=completed,
        has_query=has_query,
        gold_star_seam_reached=seam,
    )


def test_adjudication_trace_marks_the_actual_seam_even_with_zero_candidates():
    tokens = ledger.begin_request_context("a" * 32)
    try:
        ledger.begin_composition_attempt()
        trace = ledger.build_adjudication_trace({"candidates": []})
        state = ledger.current_request_context()

        assert trace["candidate_count"] == 0
        assert state["composition_attempt_count"] == 1
        assert state["gold_star_seam_reached"] is True
        assert _classify(
            {"ok": True, "response_provenance": {"class": "deterministic_recovery"}},
            seam=state["gold_star_seam_reached"],
        ) == "gold_star_seam_reached"
    finally:
        ledger.end_request_context(tokens)


def test_composer_retries_remain_one_request_level_seam_observation():
    tokens = ledger.begin_request_context("b" * 32)
    try:
        ledger.begin_composition_attempt()
        ledger.begin_composition_attempt()
        ledger.build_adjudication_trace({"candidates": []})
        state = ledger.current_request_context()

        assert state["composition_attempt_count"] == 2
        assert state["gold_star_seam_reached"] is True
        # The request correlation token is unchanged across both attempts.
        assert state["request_id"] == "b" * 32
    finally:
        ledger.end_request_context(tokens)


def test_safety_bypass_is_explicit():
    assert _classify({"intent": "SAFETY_INTERRUPT"}) == "safety_bypass"
    assert _classify({"intent": "SAFETY_CONVERSATION"}) == "safety_bypass"


def test_deterministic_answer_bypass_requires_explicit_provenance():
    assert _classify({
        "response_provenance": {"class": "deterministic_recovery"},
    }) == "deterministic_answer_bypass"
    assert _classify({
        "response_provenance": {"class": "deterministic_by_design"},
    }) == "deterministic_answer_bypass"
    assert _classify({"ok": True, "response": "answer"}) == "unclassified"


def test_native_handoff_requires_native_return_contract():
    assert _classify({
        "handoff_pending": True,
        "return_mode": "native_catalogue_search",
    }) == "native_handoff"
    assert _classify({
        "handoff_pending": True,
        "return_mode": "specialist_unknown",
    }) == "unclassified"


def test_specialist_delegation_requires_explicit_delegation_metadata():
    assert _classify({"formation_delegation": {"state": "available"}}) == "specialist_delegation"
    assert _classify({"systems_delegation": {"state": "available"}}) == "specialist_delegation"
    assert _classify({"intent": "FORMATION_HANDOFF"}) == "unclassified"


def test_invalid_failed_and_incomplete_requests_are_not_counted_as_eligible():
    assert _classify({"ok": False}, has_query=False) == "invalid_or_empty_request"
    assert _classify({"ok": False}, status=503) == "request_error"
    assert _classify({"ok": True}, completed=False) == "boundary_incomplete"


def test_unknown_routes_stay_unclassified_and_all_results_are_allowlisted():
    values = [
        _classify(None),
        _classify({"ok": True}),
        _classify({"handoff_pending": True}),
        _classify({"response_provenance": {"class": "llm"}}),
    ]
    assert set(values) == {"unclassified"}
    assert set(values).issubset(ledger.REQUEST_ELIGIBILITY_DISPOSITIONS)


def test_request_ledger_exposes_only_content_free_seam_state():
    tokens = ledger.begin_request_context("c" * 32)
    try:
        state = ledger.current_request_context()
        assert state["gold_star_seam_reached"] is False
        assert "query" not in state
        assert "question" not in state
        assert "answer" not in state
        assert "response" not in state
    finally:
        ledger.end_request_context(tokens)
