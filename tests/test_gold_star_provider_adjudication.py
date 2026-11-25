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


def test_selected_candidate_requires_complete_disposition_and_exact_answer_span():
    response = "Separate what was observed from what is inferred, then test the evidence."
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "redundant_contribution"},
            ],
            "application_evidence_spans": [{"candidate_id": "lesson-a", "span": "Separate what was observed from what is inferred"}],
        },
        response=response,
        candidates=CANDIDATES,
    )
    assert result["status"] == "provider_reported_selected"
    assert result["selected_candidate_ids"] == ["lesson-a"]
    assert result["reasoning_discipline_ids"] == ["evidence_discernment"]
    assert result["application_evidence_present"] is True
    assert result["application"] == "provider_asserted_span_present"


def test_reject_all_requires_reason_for_every_candidate():
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "reject", "reason_code": "subject_mismatch"},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "boundary_mismatch"},
            ],
            "application_evidence_spans": [],
        },
        response="A substantive answer that does not use either lesson.",
        candidates=CANDIDATES,
    )
    assert result["status"] == "provider_reported_rejected_all"
    assert result["selected_candidate_ids"] == []
    assert len(result["rejection_reason_codes"]) == 2
    assert result["application"] == "not_observed"


def test_incomplete_or_unknown_candidate_adjudication_fails_closed():
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "unknown", "decision": "select", "reason_code": None},
            ],
            "application_evidence_spans": [{"candidate_id": "lesson-a", "span": "Some exact answer text here"}],
        },
        response="Some exact answer text here",
        candidates=CANDIDATES,
    )
    assert result["status"] == "not_observed"
    assert result["selected_candidate_ids"] == []
    assert result["application"] == "not_observed"


def test_span_must_be_exactly_present_and_bounded():
    result = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "lexical_overlap_only"},
            ],
            "application_evidence_spans": [{"candidate_id": "lesson-a", "span": "This phrase is not in the answer."}],
        },
        response="The answer is otherwise substantive and sufficiently long.",
        candidates=CANDIDATES,
    )
    assert result["status"] == "provider_reported_selected"
    assert result["application_evidence_present"] is False
    assert result["application"] == "not_observed"


def test_trace_keeps_provider_report_distinct_from_human_review_and_tracks_retention():
    initial = trace.build_adjudication_trace({"candidates": CANDIDATES})
    report = adjudication.normalize_provider_adjudication(
        {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None},
                {"candidate_id": "lesson-b", "decision": "reject", "reason_code": "redundant_contribution"},
            ],
            "application_evidence_spans": [{"candidate_id": "lesson-a", "span": "Separate what was observed from what is inferred"}],
        },
        response="Separate what was observed from what is inferred, then test the evidence.",
        candidates=CANDIDATES,
    )
    traced = trace.mark_provider_adjudication(initial, report)
    composed = trace.mark_composition_result(
        traced, provider_result={"parsed": {"response": "Separate what was observed from what is inferred."}}
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



def test_output_contract_is_compact_and_preserves_all_evidence_requirements():
    contract = adjudication.build_adjudication_output_contract(CANDIDATES)
    assert len(contract) < 1100
    for required in (
        "adaptive_adjudication",
        "Preserve response",
        "doorway_title",
        "response_shape",
        "adjudication is additional",
        "candidate_assessments",
        "application_evidence_spans",
        "lesson-a",
        "lesson-b",
        "select/reject",
        "abstention boundary",
        "exact contiguous 12–240 character span",
        "No hidden reasoning or chain-of-thought",
        "paired evaluation",
    ):
        assert required in contract


def test_output_contract_is_absent_without_candidates():
    assert adjudication.build_adjudication_output_contract([]) == ""
