from visitor_failure_recovery import compose_visitor_failure_recovery


def test_transformation_rebranding_question_gets_bounded_substantive_recovery():
    result = compose_visitor_failure_recovery(
        "When does transformation become mere rebranding?"
    )
    response = result["response"]
    assert "decision rights" in response
    assert "incentives" in response
    assert "durable" in response
    assert "not presented as a synthesis" in response
    assert "canonical doorway has been inferred" in response
    assert result["basis_explanation"]


def test_unknown_question_gets_transparent_nonempty_recovery_not_fake_answer():
    result = compose_visitor_failure_recovery(
        "How should our town prepare for a changing climate?"
    )
    response = result["response"]
    assert response
    assert "couldn't complete the full answer" in response
    assert "don't want to invent" in response
    assert "not a substantive answer" in response
    assert "Living Archive" in result["basis_explanation"]


def test_recovery_preserves_question_context_without_echoing_or_mutating_it():
    question = "What makes institutional learning real?"
    result = compose_visitor_failure_recovery(question)
    assert question == "What makes institutional learning real?"
    assert "Your question is still intact" in result["response"]


def test_runtime_failure_branch_routes_through_shared_visitor_finalizer():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(
        encoding="utf-8"
    )
    start = source.index("# Universal visitor failure containment:")
    end = source.index("explicit_formation_route =", start)
    branch = source[start:end]
    assert "compose_visitor_failure_recovery(query)" in branch
    assert "_guide_finalize_visitor_payload(_visitor_payload, query)" in branch
    assert "return await _use_send_json(send, _visitor_payload, 200)" in branch
    assert branch.index("_guide_finalize_visitor_payload") < branch.index(
        "_use_send_json(send, _visitor_payload, 200)"
    )


def test_runtime_failure_branch_keeps_original_question_and_no_fabricated_destination():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(
        encoding="utf-8"
    )
    start = source.index("# Universal visitor failure containment:")
    end = source.index("explicit_formation_route =", start)
    branch = source[start:end]
    assert '"query": query' in branch
    assert '"recommendation": None' in branch
    assert '"canonical_doorway": None' in branch
