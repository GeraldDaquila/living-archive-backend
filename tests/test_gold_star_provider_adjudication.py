import gold_star_provider_adjudication as adjudication
import gold_star_adjudication_trace as trace


CANDIDATES = [
    {
        "benchmark_id": "lesson-a",
        "reasoning_family": "evidence_discernment",
        "discipline": "Separate observation from inference.",
        "abstention_boundary": "Do not infer intent from ambiguous evidence.",
    },
    {
        "benchmark_id": "lesson-b",
        "reasoning_family": "causal_analysis",
        "discipline": "Test alternative mechanisms.",
        "abstention_boundary": "Do not claim causation from correlation alone.",
    },
]


def _offset(candidate_id, response, phrase=None):
    if phrase is None:
        return {"candidate_id": candidate_id, "start": 0, "end": 0}
    start = response.index(phrase)
    return {"candidate_id": candidate_id, "start": start, "end": start + len(phrase)}


def test_selected_candidate_requires_complete_disposition_and_validated_answer_offsets():
    response = "Separate what was observed from what is inferred, then test the evidence."
    phrase = "Separate what was observed from what is inferred"
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "redundant_contribution"},
            ],
            "application_evidence_spans": [
                _offset("lesson-a", response, phrase),
                _offset("lesson-b", response),
            ],
        },
        response=response,
        candidates=CANDIDATES,
    )
    assert result["status"] == "provider_reported_selected"
    assert result["selected_candidate_ids"] == ["lesson-a"]
    assert result["reasoning_discipline_ids"] == ["evidence_discernment"]
    assert result["application_evidence_present"] is True
    assert result["application"] == "provider_asserted_span_present"
    assert result["application_evidence_reason"] == "exact_selected_offsets_validated"


def test_reject_all_requires_reason_and_zero_offsets_for_every_candidate():
    response = "A substantive answer that does not use either lesson."
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "reject", "reason_code": "subject_mismatch"},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "boundary_mismatch"},
            ],
            "application_evidence_spans": [
                _offset("lesson-a", response),
                _offset("lesson-b", response),
            ],
        },
        response=response,
        candidates=CANDIDATES,
    )
    assert result["status"] == "provider_reported_rejected_all"
    assert result["selected_candidate_ids"] == []
    assert len(result["rejection_reason_codes"]) == 2
    assert result["application"] == "not_observed"
    assert result["application_evidence_reason"] == "no_selected_candidates"


def test_incomplete_or_unknown_candidate_adjudication_fails_closed():
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "unknown", "decision": "select", "reason_code": None},
            ],
            "application_evidence_spans": [{"candidate_id": "lesson-a", "start": 0, "end": 20}],
        },
        response="Some exact answer text here",
        candidates=CANDIDATES,
    )
    assert result["status"] == "not_observed"
    assert result["selected_candidate_ids"] == []
    assert result["application"] == "not_observed"


def test_offsets_must_be_bounded_inside_the_final_response():
    response = "The answer is otherwise substantive and sufficiently long."
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "lexical_overlap_only"},
            ],
            "application_evidence_spans": [
                {"candidate_id": "lesson-a", "start": 1000, "end": 1030},
                _offset("lesson-b", response),
            ],
        },
        response=response,
        candidates=CANDIDATES,
    )
    assert result["status"] == "provider_reported_selected"
    assert result["application_evidence_present"] is False
    assert result["application"] == "not_observed"
    assert result["application_evidence_reason"] == "selected_offset_outside_final_response"


def test_selected_without_valid_offsets_can_be_delivered_but_never_earns_application_credit():
    response = "Separate what was observed from what is inferred, then test the evidence."
    initial = trace.build_adjudication_trace({"candidates": CANDIDATES})
    report = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "redundant_contribution"},
            ],
            "application_evidence_spans": [
                _offset("lesson-a", response),
                _offset("lesson-b", response),
            ],
        },
        response=response,
        candidates=CANDIDATES,
    )
    traced = trace.mark_provider_adjudication(initial, report)
    composed = trace.mark_composition_result(
        traced, provider_result={"parsed": {"response": response}}
    )
    delivered = trace.mark_final_delivery(
        composed, provider_candidate_delivered=True, final_provenance="llm"
    )
    assert delivered["selection"] == "provider_reported_selected"
    assert delivered["application_evidence_present"] is False
    assert delivered["application"] == "not_observed"
    assert delivered["contribution_retained"] == "not_verified"
    assert delivered["outcome"] == "not_evaluated"
    assert trace.validate_trace(delivered)["valid"] is True


def test_trace_keeps_provider_report_distinct_from_human_review_and_tracks_retention():
    response = "Separate what was observed from what is inferred, then test the evidence."
    phrase = "Separate what was observed from what is inferred"
    initial = trace.build_adjudication_trace({"candidates": CANDIDATES})
    report = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "redundant_contribution"},
            ],
            "application_evidence_spans": [
                _offset("lesson-a", response, phrase),
                _offset("lesson-b", response),
            ],
        },
        response=response,
        candidates=CANDIDATES,
    )
    traced = trace.mark_provider_adjudication(initial, report)
    composed = trace.mark_composition_result(
        traced, provider_result={"parsed": {"response": response}}
    )
    delivered = trace.mark_final_delivery(
        composed, provider_candidate_delivered=True, final_provenance="llm"
    )
    assert delivered["selection"] == "provider_reported_selected"
    assert delivered["application"] == "provider_asserted_span_present"
    assert delivered["contribution_retained"] == "provider_asserted_span_retained"
    assert delivered["outcome"] == "not_evaluated"
    assert trace.validate_trace(delivered)["valid"]


def test_deterministic_replacement_cannot_claim_retained_adaptation():
    initial = trace.build_adjudication_trace({"candidates": CANDIDATES})
    traced = trace.mark_provider_adjudication(
        initial,
        {
            "status": "provider_reported_selected",
            "selected_candidate_ids": ["lesson-a"],
            "rejection_reason_codes": [{"candidate_id": "lesson-b", "reason_code": "redundant_contribution"}],
            "reasoning_discipline_ids": ["evidence_discernment"],
            "application_evidence_present": True,
            "application_evidence_candidate_ids": ["lesson-a"],
            "application": "provider_asserted_span_present",
        },
    )
    final = trace.mark_final_delivery(
        traced, provider_candidate_delivered=False, final_provenance="deterministic_recovery"
    )
    assert final["contribution_retained"] == "not_retained"
    assert final["outcome"] == "not_evaluated"
    assert trace.validate_trace(final)["valid"]


def test_offsets_select_the_exact_multiline_answer_substring():
    response = "Separate what was observed\nfrom what is inferred, then test the evidence."
    phrase = "Separate what was observed\nfrom what is inferred"
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "redundant_contribution"},
            ],
            "application_evidence_spans": [
                _offset("lesson-a", response, phrase),
                _offset("lesson-b", response),
            ],
        },
        response=response,
        candidates=CANDIDATES,
    )
    assert result["application"] == "provider_asserted_span_present"
    assert result["application_evidence_reason"] == "exact_selected_offsets_validated"


def test_partial_offset_coverage_and_rejected_candidate_offsets_fail_closed():
    response = "Separate what was observed from what is inferred, then test the evidence."
    phrase = "Separate what was observed from what is inferred"
    base_report = {
        "candidate_assessments": [
            {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
            {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "redundant_contribution"},
        ],
    }
    partial = adjudication.normalize_provider_adjudication(
        {**base_report, "application_evidence_spans": [
            _offset("lesson-a", response, phrase)
        ]},
        response=response,
        candidates=CANDIDATES,
    )
    assert partial["application"] == "not_observed"
    assert partial["application_evidence_reason"] == "offset_entry_count_mismatch"
    contaminated = adjudication.normalize_provider_adjudication(
        {**base_report, "application_evidence_spans": [
            _offset("lesson-a", response, phrase),
            {"candidate_id": "lesson-b", "start": 0, "end": 10},
        ]},
        response=response,
        candidates=CANDIDATES,
    )
    assert contaminated["application"] == "not_observed"
    assert contaminated["application_evidence_reason"] == "rejected_offset_not_empty"


def test_output_contract_is_compact_and_preserves_all_evidence_requirements():
    contract = adjudication.build_adjudication_output_contract(CANDIDATES)
    assert len(contract) < 1600
    assert contract.endswith(
        "Output one object, not adjudication alone: "
        '{"response":"complete visitor answer","doorway_title":"title or empty",'
        '"response_shape":"shape","adaptive_adjudication":'
        '{"candidate_assessments":[...],"application_evidence_spans":[...]}}.'
    )
    for required in (
        "adaptive_adjudication",
        "doorway_title",
        "response_shape",
        "candidate_assessments",
        "application_evidence_spans",
        "lesson-a",
        "lesson-b",
        "select/reject",
        "abstention boundary",
        "offset object per candidate ID",
        "zero-based Unicode character start/end offsets",
        "rejected IDs use 0,0",
        "reject-all uses 0,0",
        "activation scope",
        "semantically equivalent question",
        "After drafting the final response",
        "distinctive operation",
        "exact answer substring",
        "No hidden reasoning or chain-of-thought",
        "paired evaluation",
    ):
        assert required in contract


def test_output_contract_is_absent_without_candidates():
    assert adjudication.build_adjudication_output_contract([]) == ""
