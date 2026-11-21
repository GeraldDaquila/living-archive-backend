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
    return next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


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
