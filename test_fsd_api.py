import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import fsd_api


REPORT = {
    "summary": "A bounded synthesis supported by the evidence.",
    "recurring_condition": "Information does not consistently reach corrective authority.",
    "reported_signal": "The selected scale reports a correction difficulty.",
    "strengths": ["The condition can be recognized."],
    "enabling_conditions": ["Relevant information is available."],
    "constraints": ["Corrective authority is unclear."],
    "next_steps": ["Examine one decision and its consequences."],
    "evidence_ids": ["E01", "E02"],
}


def analysis():
    return {
        "validated": {
            "scale": "organization",
            "quantum_summaries": {
                "Q001_CORRESPONDENCE": {"label": "Correspondence", "mean_constraint_signal": 1.0, "answered_items": 4},
                "Q002_CORRECTABILITY": {"label": "Correctability", "mean_constraint_signal": 2.0, "answered_items": 6},
            },
        },
        "evidence": [
            {"evidence_id": "E01", "quantum_id": "Q001_CORRESPONDENCE", "title": "Source one", "url": "https://geralddaquila.com/one", "excerpt": "Evidence one."},
            {"evidence_id": "E02", "quantum_id": "Q002_CORRECTABILITY", "title": "Source two", "url": "https://geralddaquila.com/two", "excerpt": "Evidence two."},
        ],
    }


def test_report_composition_uses_dedicated_operation_and_returns_server_sources(monkeypatch):
    calls = {}

    def fake_execute(**kwargs):
        calls.update(kwargs)
        return {"ok": True, "result": REPORT}

    monkeypatch.setattr(fsd_api, "execute_provider_gateway", fake_execute)
    result = fsd_api._compose_report(
        {"answers": [0] * 10},
        analysis(),
        object(),
    )
    assert calls["operation"] == "fsd_report_composition"
    assert calls["schema"]["name"] == "fsd_two_quantum_report"
    prompt_payload = __import__("json").loads(calls["messages"][1]["content"])
    assert len(prompt_payload["reported_answers"]) == 10
    assert "selected_response" in prompt_payload["reported_answers"][0]
    assert "answer_selections" not in prompt_payload
    assert prompt_payload["diagnostic_quanta"] == [
        {"quantum_id": "Q001_CORRESPONDENCE", "label": "Correspondence"},
        {"quantum_id": "Q002_CORRECTABILITY", "label": "Correctability"},
    ]
    assert "quantum_summaries" not in result
    assert result["report"]["scope"]["organization"] == "reported_signal"
    assert result["report"]["scope"]["civilization"] == "not_assessed"
    assert result["report"]["evidence"] == [
        {"evidence_id": "E01", "title": "Source one", "url": "https://geralddaquila.com/one"},
        {"evidence_id": "E02", "title": "Source two", "url": "https://geralddaquila.com/two"},
    ]


def test_report_composition_fails_closed_without_both_quantum_evidence_sets():
    incomplete = analysis()
    incomplete["evidence"] = incomplete["evidence"][:1]
    with pytest.raises(HTTPException) as error:
        fsd_api._compose_report({"answers": [0] * 10}, incomplete, object())
    assert error.value.status_code == 422


def test_provider_exhaustion_returns_bounded_unavailable_response(monkeypatch):
    monkeypatch.setattr(
        fsd_api,
        "execute_provider_gateway",
        lambda **kwargs: {"ok": False, "error": "provider_bank_exhausted"},
    )
    with pytest.raises(HTTPException) as error:
        fsd_api._compose_report({"answers": [0] * 10}, analysis(), object())
    assert error.value.status_code == 503
    assert error.value.detail == {"code": "fsd_provider_bank_unavailable"}


def test_rate_limit_is_enforced_per_server_side_client_key():
    key = "fsd-test-rate-limit"
    fsd_api._RATE_EVENTS.pop(key, None)
    for _ in range(fsd_api.RATE_MAX_REQUESTS):
        fsd_api._check_rate_limit(key)
    with pytest.raises(HTTPException) as error:
        fsd_api._check_rate_limit(key)
    assert error.value.status_code == 429
    fsd_api._RATE_EVENTS.pop(key, None)


def test_fsd_route_registers_once_on_existing_app():
    app = FastAPI()
    use_core = object()
    before = len(app.routes)
    fsd_api.register_fsd_routes(app, use_core)
    first_count = len(app.routes)
    fsd_api.register_fsd_routes(app, use_core)
    assert first_count == before + 1
    assert len(app.routes) == first_count
    route = next(item for item in app.routes if getattr(item, "path", None) == "/api/fsd/analyze")
    assert "POST" in route.methods


def test_http_route_enforces_authentication_and_request_size(monkeypatch):
    app = FastAPI()
    fsd_api.register_fsd_routes(app, object())
    client = TestClient(app)

    def authorize(token):
        if token != "test-server-key":
            raise HTTPException(status_code=401, detail="unauthorized")

    monkeypatch.setattr(fsd_api, "authorize_provider_gateway", authorize)
    monkeypatch.setattr(fsd_api, "_run_analysis", lambda payload, use_core: {"ok": True})

    denied = client.post("/api/fsd/analyze", json={}, headers={"X-Living-Archive-Provider-Key": "wrong"})
    assert denied.status_code == 401

    accepted = client.post(
        "/api/fsd/analyze",
        json={"contract_version": "test"},
        headers={"X-Living-Archive-Provider-Key": "test-server-key"},
    )
    assert accepted.status_code == 200
    assert accepted.json() == {"ok": True}

    oversized = client.post(
        "/api/fsd/analyze",
        content=b'{"payload":"' + (b"x" * fsd_api.MAX_BODY_BYTES) + b'"}',
        headers={
            "Content-Type": "application/json",
            "X-Living-Archive-Provider-Key": "test-server-key",
        },
    )
    assert oversized.status_code == 413


def test_end_to_end_analysis_retrieves_both_quanta_and_returns_validated_report(monkeypatch):
    retrieval_queries = []

    class FakeUseCore:
        def fetch_canonical_context(self, query):
            retrieval_queries.append(query)
            if "Correspondence" in query:
                title, url = "Correspondence source", "https://geralddaquila.com/correspondence"
            else:
                title, url = "Correctability source", "https://geralddaquila.com/correctability"
            return {
                "context_blocks": (
                    f"Title: {title}\nURL: {url}\n"
                    "Content: Canonical evidence supporting the examined systemic condition."
                )
            }

    monkeypatch.setattr(
        fsd_api,
        "execute_provider_gateway",
        lambda **kwargs: {"ok": True, "result": {**REPORT, "evidence_ids": ["E01", "E02"]}},
    )
    payload = {
        "contract_version": "fsd-two-quantum-v1",
        "answers": [0, 1, 2, 3, 0, 1, 2, 3, 0, 1],
        "scale": "organization",
    }
    result = fsd_api._run_analysis(payload, FakeUseCore())

    assert len(retrieval_queries) == 2
    assert "Correspondence" in retrieval_queries[0]
    assert "Correctability" in retrieval_queries[1]
    assert result["ok"] is True
    assert "quantum_summaries" not in result
    assert result["report"]["scope"]["organization"] == "reported_signal"
    assert [item["url"] for item in result["report"]["evidence"]] == [
        "https://geralddaquila.com/correspondence",
        "https://geralddaquila.com/correctability",
    ]


def test_end_to_end_analysis_fails_closed_when_one_quantum_has_no_evidence(monkeypatch):
    class IncompleteUseCore:
        def fetch_canonical_context(self, query):
            if "Correspondence" in query:
                return {
                    "context_blocks": (
                        "Title: Correspondence source\n"
                        "URL: https://geralddaquila.com/correspondence\n"
                        "Content: Canonical correspondence evidence."
                    )
                }
            return {"context_blocks": "", "evidence_sufficiency_unavailable": True}

    monkeypatch.setattr(
        fsd_api,
        "execute_provider_gateway",
        lambda **kwargs: {"ok": True, "result": REPORT},
    )
    payload = {
        "contract_version": "fsd-two-quantum-v1",
        "answers": [0] * 10,
        "scale": "self",
    }
    with pytest.raises(HTTPException) as error:
        fsd_api._run_analysis(payload, IncompleteUseCore())
    assert error.value.status_code == 422
    assert error.value.detail == {"code": "insufficient_independent_quantum_evidence"}
