import asyncio

import gold_star_adjudication_trace as trace
import general_guide_composition as composition


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
        trace.build_adjudication_trace(None)
        return {"response": "Deterministic response.", "provider": "registered"}
    monkeypatch.setattr(composition, "_compose_impl", deterministic_early_return)
    token = trace.begin_request_context("abcdef0123456789abcdef0123456789")
    try:
        result = composition.compose(use_core=None, query="A valid question?", context_data={})
        attached = result["_gold_star_adjudication_trace"]
        assert attached["request_id"] == "abcdef0123456789abcdef0123456789"
        assert attached["attempt_ordinal"] == 1
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
