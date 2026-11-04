import json

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import fsd_episode_api


def episode():
    return {
        "contract_version": "fsd-episode-v1",
        "scale": "institution",
        "prior_understanding": "clear",
        "experience_type": "observed_outcome",
        "consequence_significance": "material_outcome_or_decision",
        "understanding_after": "revised",
        "reconsideration_basis": "directly_changed_explanation",
        "subsequent_response": "decision_or_action_changed",
        "understanding_action_link": "directly_informed",
        "response_available": "yes",
        "non_change_reason": "not_applicable",
    }


REPORT = {
    "summary": "The respondent describes one episode in which an outcome prompted reconsideration and action.",
    "episode_observation": "The respondent reports a changed understanding followed by a related decision.",
    "strengths": ["The experience was recognized."],
    "enabling_conditions": ["Evidence was available."],
    "constraints": [],
    "next_steps": ["Compare the account with independent records where appropriate."],
    "archive_reference_ids": ["A01"],
}


class FakeUseCore:
    def fetch_canonical_context(self, query):
        if "Correspondence" in query:
            return {"context_blocks": "Title: Correspondence\nURL: https://geralddaquila.com/correspondence\nContent: Conceptual explanation of correspondence."}
        return {"context_blocks": "Title: Correctability\nURL: https://geralddaquila.com/correctability\nContent: Conceptual explanation of correctability."}


def test_episode_analysis_uses_conceptual_archive_references_not_episode_evidence(monkeypatch):
    calls = {}
    def execute(**kwargs):
        calls.update(kwargs)
        return {"ok": True, "result": REPORT}
    monkeypatch.setattr(fsd_episode_api, "execute_provider_gateway", execute)
    result = fsd_episode_api._run_episode_analysis(episode(), FakeUseCore())
    prompt = json.loads(calls["messages"][1]["content"])
    assert calls["operation"] == "fsd_report_composition"
    assert "living_archive_conceptual_context_only" in prompt
    assert "respondent_reported_episode" in prompt
    assert result["report"]["episode_provenance"]["independently_verified"] is False
    assert result["report"]["archive_references"][0]["role"] == "conceptual_context_only"
    assert result["report"]["episode_interpretation"]["overall"] == "both_transitions_reported"


def test_episode_analysis_continues_without_archive_context(monkeypatch):
    class NoArchive:
        def fetch_canonical_context(self, query):
            raise RuntimeError("retrieval unavailable")
    monkeypatch.setattr(fsd_episode_api, "execute_provider_gateway", lambda **kwargs: {
        "ok": True, "result": {**REPORT, "archive_reference_ids": []}
    })
    result = fsd_episode_api._run_episode_analysis(episode(), NoArchive())
    assert result["ok"] is True
    assert result["report"]["archive_references"] == []


def test_invalid_episode_is_rejected_before_retrieval_or_provider(monkeypatch):
    class MustNotRun:
        def fetch_canonical_context(self, query):
            raise AssertionError("retrieval must not run")
    monkeypatch.setattr(fsd_episode_api, "execute_provider_gateway", lambda **kwargs: (_ for _ in ()).throw(AssertionError("provider must not run")))
    invalid = {**episode(), "scale": "organization"}
    with pytest.raises(HTTPException) as error:
        fsd_episode_api._run_episode_analysis(invalid, MustNotRun())
    assert error.value.status_code == 400


def test_route_registers_once_on_existing_app(monkeypatch):
    app = FastAPI()
    fsd_episode_api._REGISTERED_APPS.clear()
    fsd_episode_api.register_fsd_episode_routes(app, object())
    count = len(app.routes)
    fsd_episode_api.register_fsd_episode_routes(app, object())
    assert len(app.routes) == count
    route = next(item for item in app.routes if getattr(item, "path", None) == "/api/fsd/analyze-episode")
    assert "POST" in route.methods


def test_http_route_auth_and_no_store_headers(monkeypatch):
    app = FastAPI()
    fsd_episode_api._REGISTERED_APPS.clear()
    fsd_episode_api.register_fsd_episode_routes(app, object())
    client = TestClient(app)
    monkeypatch.setattr(fsd_episode_api, "authorize_provider_gateway", lambda token: None if token == "secret" else (_ for _ in ()).throw(HTTPException(status_code=401)))
    monkeypatch.setattr(fsd_episode_api, "_run_episode_analysis", lambda payload, use_core: {"ok": True})
    denied = client.post("/api/fsd/analyze-episode", json=episode(), headers={"X-Living-Archive-Provider-Key": "bad"})
    assert denied.status_code == 401
    accepted = client.post("/api/fsd/analyze-episode", json=episode(), headers={"X-Living-Archive-Provider-Key": "secret"})
    assert accepted.status_code == 200
    assert accepted.headers["cache-control"].startswith("no-store")


def test_episode_prompt_prevents_unsupported_strengths_and_enabling_conditions(monkeypatch):
    calls = {}
    monkeypatch.setattr(fsd_episode_api, "execute_provider_gateway", lambda **kwargs: (calls.update(kwargs) or {"ok": True, "result": {**REPORT, "archive_reference_ids": []}}))
    fsd_episode_api._run_episode_analysis(episode(), FakeUseCore())
    prompt = calls["messages"][0]["content"]
    assert "Do not invent strengths or enabling conditions" in prompt
    assert "otherwise return an empty list" in prompt
    assert "suggestions, not claims about what happened" in prompt
