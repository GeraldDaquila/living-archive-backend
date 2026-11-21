import asyncio
import ast
from pathlib import Path

import gold_star_adjudication_trace as trace
from gold_star_adjudication_trace import (
    mark_composition_result,
    mark_final_delivery,
    mark_guidance_exposure,
)


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



def test_composition_return_and_final_delivery_are_distinct_evidence_stages():
    initial = trace.build_adjudication_trace(_contribution())
    composed = mark_composition_result(
        initial,
        provider_result={"parsed": {"response": "A generated answer."}},
    )
    assert composed["composition"] == "provider_candidate_returned"
    assert composed["selection"] == "not_observed"
    assert composed["application"] == "not_observed"
    assert composed["outcome"] == "not_evaluated"

    final = mark_final_delivery(
        composed,
        provider_candidate_delivered=True,
        final_provenance="llm",
    )
    assert final["final_delivery"] == "provider_candidate_delivered"
    assert final["final_provenance"] == "llm"
    assert final["application"] == "not_observed"
    assert final["outcome"] == "not_evaluated"


def test_final_deterministic_rewrite_does_not_inherit_llm_delivery_credit():
    initial = trace.build_adjudication_trace(_contribution())
    composed = mark_composition_result(
        initial,
        provider_result={"parsed": {"response": "Provider answer."}},
    )
    final = mark_final_delivery(
        composed,
        provider_candidate_delivered=False,
        final_provenance="deterministic_recovery",
    )
    assert final["final_delivery"] == "deterministic_or_unresolved_replacement"
    assert final["final_provenance"] == "deterministic_recovery"
    assert final["application"] == "not_observed"
    assert final["outcome"] == "not_evaluated"


def test_guidance_exposure_is_recorded_separately_from_selection_and_application():
    initial = trace.build_adjudication_trace(_contribution())
    exposed = mark_guidance_exposure(initial, included_in_provider_prompt=True)
    assert exposed["guidance_exposure"] == "included_in_provider_prompt"
    assert exposed["selection"] == "not_observed"
    assert exposed["application"] == "not_observed"
    assert exposed["outcome"] == "not_evaluated"
    assert trace.validate_trace(exposed)["valid"]


def test_guidance_not_included_is_not_misreported_as_application():
    initial = trace.build_adjudication_trace(_contribution())
    not_exposed = mark_guidance_exposure(initial, included_in_provider_prompt=False)
    assert not_exposed["guidance_exposure"] == "not_included"
    assert not_exposed["selection"] == "not_observed"
    assert not_exposed["application"] == "not_observed"
    assert trace.validate_trace(not_exposed)["valid"]


def test_no_candidate_guidance_exposure_is_not_applicable():
    initial = trace.build_adjudication_trace(None)
    result = mark_guidance_exposure(initial, included_in_provider_prompt=False)
    assert result["guidance_exposure"] == "not_applicable"
    assert trace.validate_trace(result)["valid"]



def test_cache_reuse_resets_previous_request_provider_adjudication():
    initial = trace.build_adjudication_trace(_contribution())
    selected = trace.mark_provider_adjudication(initial, {
        "status": "provider_reported_selected",
        "selected_candidate_ids": ["lesson-one"],
        "rejection_reason_codes": [{
            "candidate_id": "lesson-two",
            "reason_code": "redundant_contribution",
        }],
        "reasoning_discipline_ids": ["evidence_discernment"],
        "application_evidence_present": True,
        "application_evidence_candidate_ids": ["lesson-one"],
        "application": "provider_asserted_span_present",
    })
    assert selected["provider_adjudication_status"] == "provider_reported_selected"

    reused = trace.mark_cache_reuse(selected)
    assert reused["composition"] == "cached_candidate_reused"
    assert reused["provider_adjudication_status"] == "not_observed"
    assert reused["selected_candidate_ids"] == []
    assert reused["rejection_reason_codes"] == []
    assert reused["reasoning_discipline_ids"] == []
    assert reused["application_evidence_present"] is False
    assert reused["application_evidence_candidate_ids"] == []
    assert reused["selection"] == "not_observed"
    assert reused["application"] == "not_observed"
    assert trace.validate_trace(reused)["valid"]


def test_cached_candidate_delivery_preserves_origin_without_claiming_new_adjudication():
    initial = trace.mark_cache_reuse(trace.build_adjudication_trace(_contribution()))
    delivered = trace.mark_final_delivery(
        initial,
        provider_candidate_delivered=False,
        final_provenance="llm",
        cached_candidate_reused=True,
    )
    assert delivered["final_delivery"] == "cached_candidate_reused"
    assert delivered["final_provenance"] == "llm"
    assert delivered["provider_adjudication_status"] == "not_observed"
    assert delivered["selection"] == "not_observed"
    assert delivered["application"] == "not_observed"
    assert delivered["contribution_retained"] == "not_verified"
    assert trace.validate_trace(delivered)["valid"]


# Request-level correlation and trace-propagation regressions.


def test_request_token_and_attempt_ordinal_are_private_trace_metadata():
    token = trace.begin_request_context("0123456789abcdef0123456789abcdef")
    try:
        first = trace.begin_composition_attempt()
        first_trace = trace.build_adjudication_trace(None)
        assert first == {"request_id": "0123456789abcdef0123456789abcdef", "attempt_ordinal": 1}
        assert first_trace["request_id"] == first["request_id"]
        assert first_trace["attempt_ordinal"] == 1
        assert trace.validate_trace(first_trace)["valid"]
        second = trace.begin_composition_attempt()
        second_trace = trace.build_adjudication_trace(None)
        assert second["attempt_ordinal"] == 2
        assert second_trace["attempt_ordinal"] == 2
        assert trace.current_request_context()["composition_attempt_count"] == 2
    finally:
        trace.end_request_context(token)


def test_request_token_rejects_nonrandom_or_malformed_values():
    for value in ("", "question-hash", "A" * 32, "0" * 31, "0" * 33):
        try:
            trace.begin_request_context(value)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed correlation tokens must fail closed.")


def test_trace_rejects_invalid_request_id_or_attempt_ordinal():
    base = trace.build_adjudication_trace(None)
    assert trace.validate_trace({**base, "request_id": "not-a-token"})["reason"] == "invalid_request_correlation_token"
    assert trace.validate_trace({**base, "attempt_ordinal": 0})["reason"] == "invalid_composition_attempt_ordinal"


def test_composition_wrapper_attaches_trace_to_early_return(monkeypatch):
    def deterministic_early_return(**_kwargs):
        initial = trace.build_adjudication_trace({"candidates": []})
        trace.mark_guidance_exposure(initial, included_in_provider_prompt=False)
        return {"response": "Deterministic response.", "provider": "registered"}
    import general_guide_composition as composition
    tracked_compose = composition._track_gold_star_composition_attempt(deterministic_early_return)
    token = trace.begin_request_context("abcdef0123456789abcdef0123456789")
    try:
        result = tracked_compose(use_core=None, query="A valid question?", context_data={})
        attached = result["_gold_star_adjudication_trace"]
        assert attached["request_id"] == "abcdef0123456789abcdef0123456789"
        assert attached["attempt_ordinal"] == 1
        assert attached["guidance_exposure"] == "not_applicable"
        assert trace.validate_trace(attached)["valid"]
    finally:
        trace.end_request_context(token)


def test_request_context_isolated_between_concurrent_async_requests():
    async def run_one(request_id):
        token = trace.begin_request_context(request_id)
        try:
            trace.begin_composition_attempt()
            await asyncio.sleep(0)
            state = trace.current_request_context()
            return state["request_id"], state["composition_attempt_count"]
        finally:
            trace.end_request_context(token)
    async def run_all():
        return await asyncio.gather(
            run_one("11111111111111111111111111111111"),
            run_one("22222222222222222222222222222222"),
        )
    assert asyncio.run(run_all()) == [
        ("11111111111111111111111111111111", 1),
        ("22222222222222222222222222222222", 1),
    ]


def test_composition_decorator_keeps_latest_trace_without_request_context():
    import general_guide_composition as composition

    def deterministic_early_return(**_kwargs):
        initial = trace.build_adjudication_trace(None)
        trace.mark_guidance_exposure(initial, included_in_provider_prompt=False)
        return {"response": "Deterministic response."}

    tracked_compose = composition._track_gold_star_composition_attempt(deterministic_early_return)
    result = tracked_compose()
    attached = result["_gold_star_adjudication_trace"]
    assert attached["guidance_exposure"] == "not_applicable"
    assert "request_id" not in attached
    assert trace.validate_trace(attached)["valid"]

def test_main_binds_shared_outcome_emitter_for_delivery_and_request_terminal():
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    aliases = [
        node for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_emit_guide_outcome" for target in node.targets)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "_emit_guide_outcome"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "general_guide_composition"
    ]
    assert len(aliases) == 1, (
        "The outer request and final-delivery boundaries must bind the shared "
        "privacy-minimized Guide outcome emitter."
    )

    emitted_events = {
        node.args[0].value
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_emit_guide_outcome"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }
    assert {
        "gold_star_adjudication_final_delivery",
        "gold_star_request_terminal",
    } <= emitted_events

    terminal_call = next(
        node for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_emit_guide_outcome"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "gold_star_request_terminal"
    )
    terminal_fields = {keyword.arg for keyword in terminal_call.keywords}
    assert {
        "provider_route_count",
        "provider_attempt_count",
        "provider_success_count",
        "provider_failure_count",
        "provider_admission_denied_count",
        "provider_terminal_state",
        "request_ledger_version",
    } <= terminal_fields

def test_request_ledger_tracks_provider_route_terminal_counts():
    token = trace.begin_request_context("33333333333333333333333333333333")
    try:
        trace.begin_composition_attempt()
        trace.build_adjudication_trace(_contribution())
        started = trace.begin_provider_route("general_guide_composition")
        assert started["attempt_ordinal"] == 1
        assert started["provider_route_ordinal"] == 1

        trace.set_provider_route_candidate_count("general_guide_composition", 3)
        trace.record_provider_candidate_attempt("general_guide_composition")
        trace.record_provider_candidate_outcome("general_guide_composition", "failure")
        trace.record_provider_candidate_attempt("general_guide_composition")
        trace.record_provider_candidate_outcome("general_guide_composition", "success")
        summary = trace.finish_provider_route("general_guide_composition", "provider_succeeded")

        assert summary["eligible_candidate_count"] == 3
        assert summary["attempt_count"] == 2
        assert summary["success_count"] == 1
        assert summary["failure_count"] == 1
        assert summary["terminal_state"] == "provider_succeeded"

        request = trace.current_request_context()
        assert request["provider_route_count"] == 1
        assert request["provider_attempt_count"] == 2
        assert request["provider_success_count"] == 1
        assert request["provider_failure_count"] == 1
        assert request["provider_terminal_state"] == "provider_succeeded"
    finally:
        trace.end_request_context(token)


def test_provider_route_wrapper_emits_correlated_exhaustion_terminal(capsys):
    import provider_bank

    token = trace.begin_request_context("44444444444444444444444444444444")
    try:
        trace.begin_composition_attempt()
        trace.build_adjudication_trace(_contribution())

        def exhausted_route(*_args, **kwargs):
            operation = kwargs["operation"]
            trace.set_provider_route_candidate_count(operation, 2)
            trace.record_provider_candidate_attempt(operation)
            trace.record_provider_candidate_outcome(operation, "failure")
            return None

        wrapped = provider_bank._track_gold_star_provider_route(exhausted_route)
        assert wrapped(operation="general_guide_composition") is None
        output = capsys.readouterr().out
        assert "gold_star_provider_route_terminal" in output
        assert "request_id=44444444444444444444444444444444" in output
        assert "request_ledger_version=2" in output
        assert "attempt_ordinal=1" in output
        assert "provider_route_ordinal=1" in output
        assert "outcome=provider_exhausted" in output
        assert "eligible_candidate_count=2" in output
        assert "attempt_count=1" in output
        assert "failure_count=1" in output
        assert trace.current_provider_route_context()["active"] is False
        assert provider_bank.route.__wrapped__ is not None
        assert "request_id=44444444444444444444444444444444" in (
            provider_bank._gold_star_provider_route_log_fields("general_guide_composition")
        )
    finally:
        trace.end_request_context(token)


def test_composer_records_provider_no_result_before_fallback():
    source = (Path(__file__).resolve().parents[1] / "general_guide_composition.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    compose = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "compose"
    )
    function_source = ast.get_source_segment(source, compose)
    no_result = function_source[function_source.index("if not result:"):]
    assert "_mark_gold_star_composition_result(" in no_result
    assert 'provider_result=None' in no_result
    assert '"gold_star_adjudication_composition"' in no_result
    assert 'provider_route_terminal_state=provider_route.get("terminal_state", "not_observed")' in no_result

def test_provider_route_wrapper_classifies_success_and_no_eligible_candidates(capsys):
    import provider_bank

    token = trace.begin_request_context("55555555555555555555555555555555")
    try:
        trace.begin_composition_attempt()
        trace.build_adjudication_trace(_contribution())

        def successful_route(*_args, **kwargs):
            operation = kwargs["operation"]
            trace.set_provider_route_candidate_count(operation, 2)
            trace.record_provider_candidate_attempt(operation)
            trace.record_provider_candidate_outcome(operation, "success")
            return {"provider": "controlled", "model": "test"}

        result = provider_bank._track_gold_star_provider_route(successful_route)(
            operation="general_guide_composition"
        )
        assert result["provider"] == "controlled"
        assert "outcome=provider_succeeded" in capsys.readouterr().out

        trace.begin_composition_attempt()
        trace.build_adjudication_trace(_contribution())

        def no_eligible_route(*_args, **kwargs):
            trace.set_provider_route_candidate_count(kwargs["operation"], 0)
            return None

        assert provider_bank._track_gold_star_provider_route(no_eligible_route)(
            operation="general_guide_composition"
        ) is None
        output = capsys.readouterr().out
        assert "outcome=no_eligible_candidate" in output
        request = trace.current_request_context()
        assert request["provider_route_count"] == 2
        assert request["provider_attempt_count"] == 1
        assert request["provider_success_count"] == 1
        assert request["provider_terminal_state"] == "no_eligible_candidate"
    finally:
        trace.end_request_context(token)


def test_provider_candidate_attempt_is_counted_only_after_quota_admission():
    source = (Path(__file__).resolve().parents[1] / "provider_bank.py").read_text(encoding="utf-8")
    start = source.index("def _quota_guarded_call(")
    end = source.index("\n\ndef _route_result", start)
    function_source = source[start:end]
    reservation = function_source.index("reservation = reserve_provider_call(")
    counted = function_source.index('_gold_star_trace.record_provider_candidate_attempt("general_guide_composition")')
    call = function_source.index("result = _call(")
    assert reservation < counted < call


def test_provider_exhaustion_trace_event_includes_provider_route_state():
    source = (Path(__file__).resolve().parents[1] / "general_guide_composition.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    compose = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "compose"
    )
    function_source = ast.get_source_segment(source, compose)
    no_result = function_source[function_source.index("if not result:"):]
    assert 'provider_route_terminal_state=provider_route.get("terminal_state", "not_observed")' in no_result
    assert 'provider_route_attempt_count=provider_route.get("attempt_count", 0)' in no_result
    assert 'provider_route_eligible_candidate_count=provider_route.get("eligible_candidate_count")' in no_result

def test_provider_route_wrapper_does_not_track_non_guide_operations(capsys):
    import provider_bank

    token = trace.begin_request_context("66666666666666666666666666666666")
    try:
        trace.begin_composition_attempt()
        trace.build_adjudication_trace(_contribution())

        def non_guide_route(*_args, **_kwargs):
            return None

        assert provider_bank._track_gold_star_provider_route(non_guide_route)(
            operation="hrn_relational"
        ) is None
        assert capsys.readouterr().out == ""
        request = trace.current_request_context()
        assert request["provider_route_count"] == 0
        assert request["provider_attempt_count"] == 0
        assert request["provider_terminal_state"] == "not_observed"
    finally:
        trace.end_request_context(token)




def test_supplemental_claim_adjudication_provider_logs_share_request_identity_without_becoming_gold_star_composition():
    import provider_bank

    token = trace.begin_request_context("77777777777777777777777777777777")
    try:
        fields = provider_bank._gold_star_provider_route_log_fields("claim_adjudication")
        assert "request_id=77777777777777777777777777777777" in fields
        assert "request_ledger_version=2" in fields
        assert "operation=claim_adjudication" in fields
        assert "attempt_ordinal=" not in fields
        assert trace.current_request_context()["provider_route_count"] == 0
    finally:
        trace.end_request_context(token)


def test_provider_log_correlation_is_absent_outside_a_visitor_request():
    import provider_bank

    assert provider_bank._gold_star_provider_route_log_fields("claim_adjudication") == ""
