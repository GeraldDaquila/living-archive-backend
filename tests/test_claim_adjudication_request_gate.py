import builtins
import sys
import types

import main


def test_non_llm_final_response_skips_provider_claim_adjudication(monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name in {"claim_adjudication", "claim_adjudication_provider"}:
            raise AssertionError("provider claim adjudication must not run for deterministic recovery")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    result = main._adjudicate_final_visitor_claims(
        "A deterministic recovery answer.",
        [],
        llm_invoked=False,
        use_core=object(),
        request_deadline=123.0,
    )

    assert result["status"] == "unassessed"
    assert result["reason"] == "not_run_for_non_llm_final_response"
    assert result["claims"] == []
    assert result["claim_count"] == 0


def test_llm_final_response_runs_bounded_claim_adjudication(monkeypatch):
    captured = {}
    adjudication = types.ModuleType("claim_adjudication")
    provider_adapter = types.ModuleType("claim_adjudication_provider")

    def fake_adjudicate(response, documents, adjudicate_claims):
        captured.update(
            response=response,
            documents=documents,
            adapter=adjudicate_claims,
        )
        return {"version": "1.0", "status": "assessed", "claims": [], "claim_count": 0}

    adjudication.adjudicate_answer_claims = fake_adjudicate
    provider_adapter.build_provider_adjudicator = (
        lambda use_core, deadline: ("adapter", use_core, deadline)
    )
    monkeypatch.setitem(sys.modules, "claim_adjudication", adjudication)
    monkeypatch.setitem(sys.modules, "claim_adjudication_provider", provider_adapter)

    core = object()
    docs = [{"visitor_visible": True, "text": "public evidence"}]
    result = main._adjudicate_final_visitor_claims(
        "A provider-generated answer.",
        docs,
        llm_invoked=True,
        use_core=core,
        request_deadline=456.0,
    )

    assert result["status"] == "assessed"
    assert captured["response"] == "A provider-generated answer."
    assert captured["documents"] == docs
    assert captured["adapter"] == ("adapter", core, 456.0)
