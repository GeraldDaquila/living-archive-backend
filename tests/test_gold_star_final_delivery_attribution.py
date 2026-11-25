"""Gold Star v3 final visitor delivery attribution contract tests."""
import ast
from pathlib import Path

from gold_star_adjudication_trace import (
    build_adjudication_trace,
    mark_final_delivery,
    validate_trace,
)


ROOT = Path(__file__).resolve().parents[1]


def test_provider_candidate_delivery_is_explicit_and_not_quality_certification():
    trace = build_adjudication_trace({
        "candidates": [{"benchmark_id": "approved-example-1", "score": 0.91, "exact": False}]
    })
    delivered = mark_final_delivery(
        trace,
        provider_candidate_delivered=True,
        final_provenance="llm",
    )
    assert delivered["final_delivery"] == "provider_candidate_delivered"
    assert delivered["final_provenance"] == "llm"
    assert delivered["application"] == "not_observed"
    assert delivered["outcome"] == "not_evaluated"
    assert validate_trace(delivered)["valid"] is True


def test_deterministic_final_boundary_replacement_is_not_attributed_to_provider():
    trace = build_adjudication_trace({
        "candidates": [{"benchmark_id": "approved-example-1", "score": 0.91}]
    })
    replaced = mark_final_delivery(
        trace,
        provider_candidate_delivered=False,
        final_provenance="deterministic_recovery",
    )
    assert replaced["final_delivery"] == "deterministic_or_unresolved_replacement"
    assert replaced["final_provenance"] == "deterministic_recovery"
    assert replaced["application"] == "not_observed"
    assert replaced["outcome"] == "not_evaluated"
    assert validate_trace(replaced)["valid"] is True


def test_delivery_trace_rejects_content_and_identity_fields():
    trace = build_adjudication_trace(None)
    trace["question"] = "must never be retained"
    assert validate_trace(trace) == {
        "valid": False,
        "reason": "content_or_identity_field_prohibited",
    }


def _function(source, name):
    module = ast.parse(source)
    matches = [
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert matches, f"function not found: {name}"
    # main.py intentionally rebinds the finalizer with a shared outer wrapper.
    return matches[-1]


def test_shared_final_boundary_consumes_private_trace_before_early_returns():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    wrapper = _function(source, "_guide_finalize_visitor_payload")
    source_segment = ast.get_source_segment(source, wrapper)
    assert 'safe_input.pop("_gold_star_adjudication_trace", None)' in source_segment
    assert 'safe_input.pop("_gold_star_provider_candidate_matches_payload", False)' in source_segment
    assert "finalized = _guide_finalize_visitor_payload_inner(safe_input, query)" in source_segment
    assert "result.pop(\"_gold_star_adjudication_trace\", None)" in source_segment
    assert "result.pop(\"_gold_star_provider_candidate_matches_payload\", None)" in source_segment
    assert "gold_star_adjudication_final_delivery" in source_segment
    assert "gold_star_final_delivery_unavailable" in source_segment
    assert 'reason="finalizer_non_dict"' in source_segment
    assert 'reason="delivery_result_non_dict"' in source_segment
    assert 'reason="trace_not_initialized"' in source_segment
    assert "def _composition_attempt_count()" in source_segment
    assert "if attempt_count > 0:" in source_segment
    assert "composition_attempt_count=attempt_count" in source_segment
    assert "result_type=type(finalized).__name__" in source_segment
    assert "result_type=type(result).__name__" in source_segment


def test_non_dict_inner_finalizer_emits_explicit_unavailable_disposition(monkeypatch):
    import main
    import gold_star_adjudication_trace as ledger

    token = ledger.begin_request_context("0123456789abcdef0123456789abcdef")
    ledger.begin_composition_attempt()
    events = []
    try:
        monkeypatch.setattr(main, "_guide_finalize_visitor_payload_inner", lambda *_args: None)
        monkeypatch.setattr(
            main,
            "_emit_guide_outcome",
            lambda event, **fields: events.append((event, fields)),
        )
        result = main._guide_finalize_visitor_payload(
            {"response": "private visitor text is not telemetry"},
            "A test question?",
        )
        assert result is None
        assert len(events) == 1
        event, fields = events[0]
        assert event == "gold_star_final_delivery_unavailable"
        assert fields == {"reason": "finalizer_non_dict", "result_type": "NoneType"}
        assert not {"query", "question", "answer", "response", "user_id", "session_id"} & fields.keys()
    finally:
        ledger.end_request_context(token)


def test_safety_and_exact_gold_star_early_returns_cannot_claim_provider_delivery():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    wrapper = _function(source, "_guide_finalize_visitor_payload")
    segment = ast.get_source_segment(source, wrapper)
    assert '"SAFETY_INTERRUPT", "SAFETY_CONVERSATION"' in segment
    assert segment.count("allow_provider_delivery=False") == 2


def test_composition_candidate_carries_only_the_validated_internal_trace():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert '"_gold_star_adjudication_trace": dict(gold_star_adjudication_trace)' in source
    assert "_validate_gold_star_adjudication_trace(gold_star_adjudication_trace)" in source


def test_basic_inquiry_propagates_trace_and_recomputes_after_bounded_repair():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'payload["_gold_star_adjudication_trace"] = dict(_adjudication_trace)' in source
    assert 'payload["_gold_star_provider_candidate_matches_payload"] = bool(' in source
    assert "A bounded repair may replace the provider candidate before the shared" in source



def test_final_delivery_logs_guidance_exposure_as_a_separate_stage():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    wrapper = _function(source, "_guide_finalize_visitor_payload")
    segment = ast.get_source_segment(source, wrapper)
    assert "_mark_gold_star_guidance_exposure(" in segment
    assert '"gold_star_guidance_exposure"' in segment
    assert 'guidance_exposure=trace.get("guidance_exposure", "not_observed")' in segment


def test_gold_star_quality_event_reports_candidate_availability_not_activation():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert '"gold_star_quality_candidate_available"' in source
    assert '"gold_star_quality_active"' not in source


def test_no_composition_attempt_does_not_emit_missing_trace_failure(monkeypatch):
    import main
    import gold_star_adjudication_trace as ledger

    token = ledger.begin_request_context("abcdef0123456789abcdef0123456789")
    events = []
    try:
        monkeypatch.setattr(main, "_guide_finalize_visitor_payload_inner", lambda *_args: None)
        monkeypatch.setattr(
            main,
            "_emit_guide_outcome",
            lambda event, **fields: events.append((event, fields)),
        )
        result = main._guide_finalize_visitor_payload(
            {"response": "private visitor text is not telemetry"},
            "A deterministic early-route question?",
        )
        assert result is None
        assert events == []
    finally:
        ledger.end_request_context(token)

