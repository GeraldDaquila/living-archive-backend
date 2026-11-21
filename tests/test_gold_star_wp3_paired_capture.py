"""Safety and provenance tests for the one-shot WP3 paired capture runner."""
from types import SimpleNamespace

from scripts.guide_live_evaluation import evaluate_held
from scripts.capture_gold_star_wp3_pairs import (
    capture_deterministic_payload,
    capture_live_deterministic_payload,
    classify_deterministic_payload,
    classify_llm_payload,
    verify_runtime_identity,
    wait_for_runtime_identity,
    select_evaluation_cases,
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
    assert payload["response_provenance"]["class"] == "deterministic_recovery"
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


def test_runtime_identity_retries_transient_server_failure(monkeypatch):
    import scripts.capture_gold_star_wp3_pairs as capture

    calls = []
    responses = [
        {"status": 503, "body": None, "error": None},
        {"status": 200, "body": {
            "deployment_commit_sha": "candidate-sha",
            "version": "test",
            "fingerprint": "fingerprint",
        }},
    ]
    monkeypatch.setattr(capture, "_http_json", lambda url, **kwargs: (calls.append(kwargs) or responses.pop(0)))
    monkeypatch.setattr(capture.time, "sleep", lambda seconds: None)

    identity = verify_runtime_identity("https://mirror.example", "candidate-sha")

    assert len(calls) == 2
    assert all(call["timeout"] == 90 for call in calls)
    assert identity["deployment_commit_sha"] == "candidate-sha"


def test_runtime_identity_retries_transport_timeout_but_still_requires_matching_sha(monkeypatch):
    import scripts.capture_gold_star_wp3_pairs as capture

    calls = []
    responses = [
        {"status": None, "body": None, "error": "TimeoutError"},
        {"status": 200, "body": {
            "deployment_commit_sha": "candidate-sha",
            "version": "test",
            "fingerprint": "fingerprint",
        }},
    ]
    monkeypatch.setattr(capture, "_http_json", lambda url, **kwargs: (calls.append(kwargs) or responses.pop(0)))
    monkeypatch.setattr(capture.time, "sleep", lambda seconds: None)

    identity = verify_runtime_identity("https://mirror.example", "candidate-sha")

    assert len(calls) == 2
    assert identity["deployment_commit_sha"] == "candidate-sha"


def test_runtime_identity_does_not_retry_valid_but_mismatched_commit(monkeypatch):
    import scripts.capture_gold_star_wp3_pairs as capture

    calls = []
    monkeypatch.setattr(capture, "_http_json", lambda url, **kwargs: (
        calls.append(kwargs) or {
            "status": 200,
            "body": {"deployment_commit_sha": "other-sha"},
        }
    ))

    try:
        verify_runtime_identity("https://mirror.example", "candidate-sha")
    except RuntimeError as exc:
        assert "Source mismatch" in str(exc)
    else:
        raise AssertionError("Mismatched runtime source must not be paired.")

    assert len(calls) == 1


def test_deterministic_capture_prefers_live_task_specific_recovery():
    calls = []

    def task_recovery(query):
        calls.append(("task", query))
        return {"recovery_id": "task_test", "response": "Task-specific answer."}

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("The generic low-level fallback must not bypass task recovery.")

    def finalize(payload, query):
        calls.append(("finalizer", query))
        result = dict(payload)
        result["recommendation"] = {"title": "Irrelevant inferred doorway"}
        result["canonical_doorway"] = {"title": "Irrelevant inferred doorway"}
        return result

    fake_main = SimpleNamespace(
        _compose_task_specific_recovery=task_recovery,
        _basic_inquiry_round1_deterministic_response=should_not_run,
        _sanitize_basic_inquiry_response=lambda value: value.strip(),
        _guide_finalize_visitor_payload=finalize,
    )

    payload = capture_deterministic_payload(fake_main, "A supported task question?")

    assert calls == [("task", "A supported task question?"), ("finalizer", "A supported task question?")]
    assert payload["response"] == "Task-specific answer."
    assert payload["capture"]["path"] == "main._compose_task_specific_recovery"
    assert payload["response_provenance"]["llm_invoked"] is False
    assert payload["recommendation"] is None
    assert payload["canonical_doorway"] is None


def test_deterministic_capture_uses_registered_fact_before_generic_fallback():
    calls = []

    def fact_recovery(query):
        calls.append(("fact", query))
        return {
            "fact_id": "water_boiling_point_sea_level",
            "response": "Water boils at 100°C (212°F) at standard atmospheric pressure.",
            "doorway": None,
        }

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("A query-matched registered fact must precede generic fallback.")

    def finalize(payload, query):
        calls.append(("finalizer", query))
        result = dict(payload)
        result["recommendation"] = {"title": "Irrelevant inferred doorway"}
        result["canonical_doorway"] = {"title": "Irrelevant inferred doorway"}
        return result

    fake_main = SimpleNamespace(
        _established_general_knowledge_recovery=fact_recovery,
        _basic_inquiry_round1_deterministic_response=should_not_run,
        _sanitize_basic_inquiry_response=lambda value: value.strip(),
        _guide_finalize_visitor_payload=finalize,
    )

    payload = capture_deterministic_payload(
        fake_main,
        "At standard atmospheric pressure, what temperature does water boil at?",
    )

    assert calls[0] == ("fact", "At standard atmospheric pressure, what temperature does water boil at?")
    assert payload["response"].startswith("Water boils at 100°C")
    assert payload["capture"]["path"] == "main._established_general_knowledge_recovery"
    assert payload["recommendation"] is None
    assert payload["canonical_doorway"] is None



def test_wait_for_runtime_identity_retries_stale_mirror_commit_then_accepts_exact_sha(monkeypatch):
    import scripts.capture_gold_star_wp3_pairs as capture

    calls = []
    responses = [
        {"status": 200, "body": {"deployment_commit_sha": "previous-sha"}},
        {"status": 200, "body": {
            "deployment_commit_sha": "candidate-sha",
            "version": "test",
            "fingerprint": "fingerprint",
        }},
    ]
    monkeypatch.setattr(
        capture, "_http_json",
        lambda url, **kwargs: (calls.append(url) or responses.pop(0)),
    )
    monkeypatch.setattr(capture.time, "sleep", lambda seconds: None)

    identity = wait_for_runtime_identity(
        "https://living-archive-backend-mirror.onrender.com",
        "candidate-sha",
        timeout_seconds=30,
    )

    assert len(calls) == 2
    assert identity["deployment_commit_sha"] == "candidate-sha"


def test_wait_for_runtime_identity_fails_closed_when_mirror_never_reaches_candidate(monkeypatch):
    import scripts.capture_gold_star_wp3_pairs as capture

    monkeypatch.setattr(capture, "_http_json", lambda url, **kwargs: {
        "status": 200, "body": {"deployment_commit_sha": "previous-sha"}
    })
    monkeypatch.setattr(capture.time, "monotonic", iter([0.0, 0.0, 31.0]).__next__)
    monkeypatch.setattr(capture.time, "sleep", lambda seconds: None)

    try:
        wait_for_runtime_identity(
            "https://living-archive-backend-mirror.onrender.com",
            "candidate-sha",
            timeout_seconds=30,
        )
    except RuntimeError as exc:
        assert "Source mismatch" in str(exc) or "Timed out waiting" in str(exc)
    else:
        raise AssertionError("Capture must not proceed while QA serves an older commit.")



def test_live_deterministic_capture_uses_actual_visitor_response_and_no_llm_provenance():
    body = {
        "ok": True,
        "response": "The exact answer returned to the visitor.",
        "recommendation": None,
        "response_provenance": {
            "class": "deterministic_recovery",
            "provider": "task_specific_recovery",
            "model": None,
            "llm_invoked": False,
        },
        "route_source": "guide_early_deterministic_boundary",
        "processing": "early_deterministic_boundary",
    }
    transport = {"status": 200, "body": body}
    runtime = {"deployment_commit_sha": "candidate-sha"}

    verified, provenance = classify_deterministic_payload(body)
    captured = capture_live_deterministic_payload(body, runtime, transport)

    assert verified is True
    assert provenance["verification_basis"] == "explicit_no_llm_invocation_at_visitor_boundary"
    assert captured["response"] == body["response"]
    assert captured["capture"]["path"] == "secondary_mirror_POST_api_query_deterministic_visitor_output"
    assert captured["route_source"] == "guide_early_deterministic_boundary"


def test_unresolved_provenance_with_explicit_no_llm_invocation_is_deterministic():
    body = {
        "ok": True,
        "response": "A bounded registered-fact answer.",
        "response_provenance": {
            "class": "unresolved",
            "llm_invoked": False,
        },
    }
    assert classify_deterministic_payload(body)[0] is True


def test_missing_llm_invocation_flag_is_not_accepted_as_deterministic():
    body = {
        "ok": True,
        "response": "An answer with incomplete provenance.",
        "response_provenance": {"class": "unresolved"},
    }
    assert classify_deterministic_payload(body)[0] is False



def test_heldout_evaluator_accepts_explicit_conditional_centralization_and_delegation():
    case = {
        "case_id": "heldout-strategic-governance-001",
        "query": "Should a growing nonprofit centralize decisions or distribute authority across its teams?",
    }
    response = (
        "Use centralization when a decision creates organization-wide obligations, carries legal "
        "or material financial risk, requires consistent standards, or affects several teams at once. "
        "Use distributed authority when a decision is routine and reversible, and the relevant knowledge "
        "sits with the team doing the work and the consequences can be contained locally. A hybrid is "
        "usually the best arrangement."
    )
    checks = evaluate_held(case, {
        "status": 200,
        "error": None,
        "body": {"ok": True, "response": response, "recommendation": None},
    })
    failed = [item for item in checks if not item["passed"]]
    assert failed == []


def test_heldout_evaluator_accepts_explicit_cause_cannot_be_established_language():
    case = {
        "case_id": "heldout-uncertain-causation-001",
        "query": "What caused the sudden increase in our website traffic last week?",
    }
    response = (
        "The cause cannot be established from the information provided; the traffic increase alone "
        "is not enough to identify what changed. Compare acquisition sources, landing pages, campaigns, "
        "referrals, and server logs before drawing a conclusion."
    )
    checks = evaluate_held(case, {
        "status": 200,
        "error": None,
        "body": {"ok": True, "response": response, "recommendation": None},
    })
    failed = [item for item in checks if not item["passed"]]
    assert failed == []



def test_case_selector_supports_a_single_heldout_case_without_reordering():
    cases = [
        {"case_id": "case-a"},
        {"case_id": "case-b"},
        {"case_id": "case-c"},
    ]
    assert select_evaluation_cases(cases, ["case-b"]) == [{"case_id": "case-b"}]
    assert select_evaluation_cases(cases, ["case-c", "case-a"]) == [
        {"case_id": "case-c"}, {"case_id": "case-a"}
    ]


def test_case_selector_rejects_unknown_and_duplicate_case_ids():
    cases = [{"case_id": "case-a"}, {"case_id": "case-b"}]
    for requested in (["missing"], ["case-a", "case-a"]):
        try:
            select_evaluation_cases(cases, requested)
        except ValueError:
            pass
        else:
            raise AssertionError("Unknown or duplicate case IDs must be rejected.")


def test_capture_runner_has_no_standalone_qa_target():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "scripts/capture_gold_star_wp3_pairs.py").read_text(encoding="utf-8")
    assert "living-archive-gold-star-v2-qa.onrender.com" not in source
    assert "APPROVED_TARGETS = {MIRROR}" in source



def test_memory_probe_workflow_is_single_case_mirror_only_and_guarded():
    from pathlib import Path

    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-wp3-memory-probe.yml"
    ).read_text(encoding="utf-8")
    assert "https://living-archive-backend-mirror.onrender.com" in workflow
    assert "[wp3-memory-probe]" in workflow
    assert "--case-id heldout-strategic-governance-001" in workflow
    assert "--skip-provider-probe" in workflow
    assert "--require-http-200" in workflow
    assert "living-archive-gold-star-v2-qa.onrender.com" not in workflow
