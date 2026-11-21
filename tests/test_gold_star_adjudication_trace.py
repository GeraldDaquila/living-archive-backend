import gold_star_adjudication_trace as trace


def _contribution():
    return {
        "benchmark_id": "lesson-one",
        "candidates": [
            {"benchmark_id": "lesson-one", "score": 0.83, "exact": False},
            {"benchmark_id": "lesson-two", "score": 0.72, "exact": True},
        ],
        "authority_mode": "structural_guidance_only",
    }


def test_candidate_retrieval_is_not_reported_as_selection_or_application():
    result = trace.build_adjudication_trace(_contribution())
    assert result["state"] == "candidates_supplied"
    assert result["candidate_ids"] == ["lesson-one", "lesson-two"]
    assert result["selection"] == "not_observed"
    assert result["application"] == "not_observed"
    assert result["outcome"] == "not_evaluated"
    assert trace.validate_trace(result)["valid"]


def test_absence_of_candidates_is_distinct_from_abstention_after_adjudication():
    result = trace.build_adjudication_trace(None)
    assert result["state"] == "no_candidates"
    assert result["selection"] == "not_applicable"
    assert result["application"] == "not_observed"


def test_provider_candidate_return_does_not_self_certify_application():
    initial = trace.build_adjudication_trace(_contribution())
    result = trace.mark_composition_result(
        initial,
        provider_result={"parsed": {"response": "A substantive answer."}, "provider": "provider-x"},
    )
    assert result["composition"] == "provider_candidate_returned"
    assert result["selection"] == "not_observed"
    assert result["application"] == "not_observed"
    assert result["outcome"] == "not_evaluated"


def test_provider_exhaustion_is_recorded_without_inventing_adaptation():
    initial = trace.build_adjudication_trace(_contribution())
    result = trace.mark_composition_result(initial, provider_result=None)
    assert result["composition"] == "provider_no_result"
    assert result["selection"] == "not_observed"
    assert result["application"] == "not_observed"


def test_final_deterministic_replacement_does_not_inherit_provider_adaptation_credit():
    initial = trace.build_adjudication_trace(_contribution())
    composed = trace.mark_composition_result(
        initial,
        provider_result={"parsed": {"response": "Provider candidate."}},
    )
    delivered = trace.mark_final_delivery(
        composed,
        provider_candidate_delivered=False,
        final_provenance="deterministic_recovery",
    )
    assert delivered["final_delivery"] == "deterministic_or_unresolved_replacement"
    assert delivered["final_provenance"] == "deterministic_recovery"
    assert delivered["application"] == "not_observed"
    assert delivered["outcome"] == "not_evaluated"


def test_final_provider_delivery_is_still_not_semantic_quality_certification():
    initial = trace.build_adjudication_trace(_contribution())
    delivered = trace.mark_final_delivery(
        initial,
        provider_candidate_delivered=True,
        final_provenance="llm",
    )
    assert delivered["final_delivery"] == "provider_candidate_delivered"
    assert delivered["application"] == "not_observed"
    assert delivered["outcome"] == "not_evaluated"


def test_trace_is_content_free_and_rejects_identity_or_answer_fields():
    result = trace.build_adjudication_trace(_contribution())
    assert not {"query", "answer", "response", "user_id", "session_id"} & result.keys()
    polluted = {**result, "query": "private wording"}
    assert trace.validate_trace(polluted) == {
        "valid": False,
        "reason": "content_or_identity_field_prohibited",
    }


def test_trace_distinguishes_human_reviewed_states_from_automated_observation():
    result = trace.build_adjudication_trace(_contribution())
    assert result["selection"] != "human_reviewed_selected"
    assert result["application"] != "human_reviewed_applied"
    assert result["outcome"] != "human_reviewed_improved"
