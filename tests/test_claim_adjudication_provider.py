import json
import sys
import types

from claim_adjudication_provider import build_provider_adjudicator


def test_provider_adapter_uses_one_bounded_provider_bank_call(monkeypatch):
    captured = {}
    expected_claim = {
        "claim": "A factual claim.",
        "answer_quote": "A factual claim.",
        "outcome": "supported",
        "reason": "Directly stated.",
        "attributions": [{"passage_id": "passage-1", "quote": "Exact source sentence."}],
    }

    def fake_route(**kwargs):
        captured.update(kwargs)
        parsed = kwargs["parse"](json.dumps({"claims": [expected_claim]}))
        return parsed

    monkeypatch.setitem(sys.modules, "provider_bank", types.SimpleNamespace(route=fake_route))
    callback = build_provider_adjudicator(object(), 123.5)
    result = callback(
        "A factual claim.",
        [{"passage_id": "passage-1", "text": "Exact source sentence.", "title": "Public source", "url": "https://geralddaquila.com/public/"}],
    )

    assert result == [expected_claim]
    assert captured["operation"] == "claim_adjudication"
    assert captured["max_tokens"] == 1500
    assert captured["deadline_monotonic"] == 123.5
    assert len(captured["messages"]) == 2
    assert "A factual claim." in captured["messages"][1]["content"]


def test_provider_adapter_returns_none_for_unavailable_provider(monkeypatch):
    monkeypatch.setitem(sys.modules, "provider_bank", types.SimpleNamespace(route=lambda **_kwargs: None))
    callback = build_provider_adjudicator(object(), 123.5)
    assert callback("answer", [{"passage_id": "p1", "text": "source"}]) is None


def test_provider_adapter_rejects_malformed_json(monkeypatch):
    def fake_route(**kwargs):
        return kwargs["parse"]("not json")

    monkeypatch.setitem(sys.modules, "provider_bank", types.SimpleNamespace(route=fake_route))
    callback = build_provider_adjudicator(object(), 123.5)
    assert callback("answer", [{"passage_id": "p1", "text": "source"}]) is None
