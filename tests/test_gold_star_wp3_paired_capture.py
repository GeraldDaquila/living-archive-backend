"""Safety and provenance tests for the one-shot WP3 paired capture runner."""
from types import SimpleNamespace

from scripts.capture_gold_star_wp3_pairs import (
    capture_deterministic_payload,
    classify_llm_payload,
    verify_runtime_identity,
)


def test_llm_capture_requires_final_output_provenance_not_provider_attempts():
    assert classify_llm_payload({
        "response_provenance": {
            "class": "llm", "provider": "groq", "model": "model-x", "llm_invoked": True
        }
    })[0]
    assert classify_llm_payload({
        "answer_envelope": {
            "evidence": {"provenance_class": "llm"},
            "route": {"provider_present": True, "model_present": True},
        }
    })[0]
    assert not classify_llm_payload({"provider": "groq", "model": "model-x"})[0]
    assert not classify_llm_payload({
        "provider": "groq", "model": "model-x",
        "response_provenance": {"class": "unresolved"},
    })[0]
    assert not classify_llm_payload({"response": "An answer with no provenance."})[0]
    assert not classify_llm_payload({
        "provider": "deterministic_fallback", "model": "",
        "response_provenance": {"class": "deterministic_recovery"},
    })[0]


def test_deterministic_capture_executes_named_function_and_shared_finalizer():
    calls = []
    def deterministic(query, interpretation, context, recommendation_available=False):
        calls.append(("deterministic", query, context, recommendation_available))
        return {
            "response": "A deterministic answer.",
            "recommendation": None,
            "provider": "bounded_test_recovery",
            "model": "",
        }
    def sanitize(value):
        return value.strip()
    def finalize(payload, query):
        calls.append(("finalizer", query))
        result = dict(payload)
        result["response"] = result["response"] + " Finalized."
        return result

    fake_main = SimpleNamespace(
        _basic_inquiry_round1_deterministic_response=deterministic,
        _sanitize_basic_inquiry_response=sanitize,
        _guide_finalize_visitor_payload=finalize,
    )
    payload = capture_deterministic_payload(fake_main, "A held-out question?")
    assert calls[0][0] == "deterministic"
    assert calls[1] == ("finalizer", "A held-out question?")
    assert payload["response"] == "A deterministic answer. Finalized."
    assert payload["response_provenance"]["class"] == "deterministic_fallback"
    assert payload["capture"]["raw_response"] == "A deterministic answer."


def test_runtime_identity_mismatch_fails_closed(monkeypatch):
    import scripts.capture_gold_star_wp3_pairs as capture
    monkeypatch.setattr(capture, "_http_json", lambda url, **kwargs: {
        "status": 200,
        "body": {
            "ok": True,
            "deployment_commit_sha": "deployed-sha",
            "version": "test",
            "fingerprint": "fingerprint",
        },
    })
    try:
        verify_runtime_identity("https://mirror.example", "different-sha")
    except RuntimeError as exc:
        assert "Source mismatch" in str(exc)
    else:
        raise AssertionError("Mismatched runtime source must not be paired.")


def test_persisted_capture_fixture_keeps_unverified_llm_outputs_null():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    dataset = json.loads(
        (root / "docs/qa/gold_star_paired_fixture_template.json").read_text(encoding="utf-8")
    )
    assert dataset["source_code_commit"] == "93c2d3a31405ec8b193e8d7a986ed764415ef8d3"
    assert len(dataset["cases"]) == 7
    assert all(case["llm"] is None for case in dataset["cases"])
    assert all(case["deterministic"] for case in dataset["cases"])
    assert all(case["fixture_status"] == "deterministic_captured_llm_unverified" for case in dataset["cases"])
