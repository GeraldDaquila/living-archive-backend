import pytest
from fastapi import HTTPException

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
