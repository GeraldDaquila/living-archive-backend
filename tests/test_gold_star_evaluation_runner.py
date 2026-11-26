"""Contracts for synthetic-only Gold Star paired generation."""

import json
import pytest
from pathlib import Path

import gold_star_evaluation_runner as runner
from gold_star_evaluation_context import current_evaluation_context


def _fake_compose_factory(*, mismatch=False, rewrite=False, no_treatment_guidance=False, base_mismatch=False):
    calls = []

    def fake_compose(**kwargs):
        context = current_evaluation_context()
        calls.append((context.arm, kwargs["query"]))
        arm = context.arm
        trace = {
            "composition": "provider_candidate_returned",
            "candidate_count": 0 if arm == "control" else (
                0 if no_treatment_guidance else 1
            ),
            "guidance_exposure": (
                "not_applicable" if arm == "control"
                else "not_included" if no_treatment_guidance
                else "included_in_provider_prompt"
            ),
            "candidate_ids": [] if arm == "control" else ["candidate-1"],
            "provider_adjudication_status": "not_observed" if arm == "control" else "validated",
            "selection": "not_applicable" if arm == "control" else "selected",
            "selected_candidate_ids": [] if arm == "control" else ["candidate-1"],
            "reasoning_discipline_ids": [] if arm == "control" else ["discipline-1"],
            "application": "not_observed" if arm == "control" else "provider_reported",
            "application_evidence_present": arm == "treatment",
            "application_evidence_candidate_ids": [] if arm == "control" else ["candidate-1"],
            "contribution_retained": "not_evaluated" if arm == "control" else "provider_asserted_span_retained",
            "outcome": "not_evaluated",
        }
        return {
            "provider": "other-provider" if mismatch else context.provider,
            "model": context.model,
            "response": f"Synthetic {arm} output.",
            "doorway_title": f"Private {arm} doorway",
            "doorway_url": f"https://example.test/{arm}",
            "_gold_star_evaluation_response_unchanged": not rewrite,
            "_gold_star_evaluation_base_prompt_fingerprint": "c" * 64 if not base_mismatch or arm == "control" else "d" * 64,
            "_gold_star_evaluation_schema_fingerprint": ("e" if arm == "control" else "f") * 64,
            "_gold_star_adjudication_trace": trace,
        }

    return fake_compose, calls


@pytest.mark.parametrize(
    "generation_order",
    [("control", "treatment"), ("treatment", "control")],
)
def test_runner_generates_blinded_fresh_pair_from_fixed_heldout_case(
    monkeypatch, generation_order
):
    fake_compose, calls = _fake_compose_factory()
    monkeypatch.setattr(runner._composition, "compose", fake_compose)

    class DeterministicRandom:
        def shuffle(self, values):
            if values and isinstance(values[0], str):
                values[:] = generation_order
            else:
                values.reverse()

    monkeypatch.setattr(runner.secrets, "SystemRandom", DeterministicRandom)

    result = runner.run_synthetic_matched_pair(
        case_id="heldout-practical-trust-001",
        provider="groq",
        model="openai/gpt-oss-120b",
        runtime_commit="abc123",
        registry_sha256="a" * 64,
        use_core=object(),
    )

    assert result["ok"] is True
    assert result["persisted"] is False
    assert result["visitor_data_used"] is False
    assert result["fresh_provider_generations"] == 2
    assert [arm for arm, _query in calls] == list(generation_order)
    assert calls[0][1] == calls[1][1]
    assert current_evaluation_context() is None

    artifacts = result["blind_artifacts"]
    assert len(artifacts) == 2
    assert {item["output"] for item in artifacts} == {
        "Synthetic control output.",
        "Synthetic treatment output.",
    }
    assert all(set(item) == {"case_id", "artifact_ref", "output"} for item in artifacts)
    assert all("doorway_title" not in item and "doorway_url" not in item for item in artifacts)
    assert artifacts[0]["artifact_ref"] != artifacts[1]["artifact_ref"]
    assert all("control" not in item["artifact_ref"] and "treatment" not in item["artifact_ref"] for item in artifacts)

    manifest = result["operator_manifest"]
    assert manifest["case_id"] == "heldout-practical-trust-001"
    assert manifest["case_family"] == "practical_application"
    assert manifest["provider"] == "groq"
    assert manifest["model"] == "openai/gpt-oss-120b"
    assert manifest["base_prompt_fingerprint"] == "c" * 64
    assert manifest["provider_schema_fingerprints"] == {
        "control": "e" * 64, "treatment": "f" * 64
    }
    assert manifest["control"]["provider_schema_sha256"] == "e" * 64
    assert manifest["treatment"]["provider_schema_sha256"] == "f" * 64
    assert manifest["generation_order"] == list(generation_order)
    assert manifest["control"]["adaptation_enabled"] is False
    assert manifest["treatment"]["adaptation_enabled"] is True
    assert manifest["control"]["output_artifact_ref"] != manifest["treatment"]["output_artifact_ref"]
    assert manifest["control"]["doorway_title"] == "Private control doorway"
    assert manifest["control"]["doorway_url"] == "https://example.test/control"
    assert manifest["treatment"]["doorway_title"] == "Private treatment doorway"
    assert manifest["treatment"]["doorway_url"] == "https://example.test/treatment"
    assert manifest["treatment_guidance_candidate_count"] == 1
    assert manifest["treatment_guidance_exposure"] == "included_in_provider_prompt"
    assert manifest["control"]["adjudication"]["application_evidence_present"] is False
    assert manifest["treatment"]["adjudication"]["application_evidence_present"] is True
    assert manifest["treatment"]["adjudication"]["contribution_retained"] == "provider_asserted_span_retained"
    assert manifest["adaptation_scope"] == "approved_cross_question_structural_guidance_only"
    assert "query" not in manifest
    assert "question" not in manifest
    assert "response" not in manifest
    assert "output" not in manifest


def test_runner_rejects_case_id_outside_fixed_allowlist(monkeypatch):
    fake_compose, calls = _fake_compose_factory()
    monkeypatch.setattr(runner._composition, "compose", fake_compose)

    with pytest.raises(runner.GoldStarEvaluationRunError) as error:
        runner.run_synthetic_matched_pair(
            case_id="visitor-supplied-question",
            provider="groq",
            model="openai/gpt-oss-120b",
            runtime_commit="abc123",
            registry_sha256="a" * 64,
            use_core=object(),
        )

    assert error.value.code == "case_not_allowlisted"
    assert calls == []


@pytest.mark.parametrize(
    ("factory_kwargs", "expected_code"),
    [
        ({"mismatch": True}, "provider_model_pin_mismatch"),
        ({"rewrite": True}, "deterministic_rewrite_or_unverified_output"),
        ({"no_treatment_guidance": True}, "treatment_guidance_not_exposed"),
        ({"base_mismatch": True}, "base_prompt_fingerprint_mismatch"),
    ],
)
def test_runner_rejects_unpaired_or_non_adaptive_evidence(
    monkeypatch, factory_kwargs, expected_code
):
    fake_compose, _calls = _fake_compose_factory(**factory_kwargs)
    monkeypatch.setattr(runner._composition, "compose", fake_compose)

    with pytest.raises(runner.GoldStarEvaluationRunError) as error:
        runner.run_synthetic_matched_pair(
            case_id="heldout-practical-trust-001",
            provider="groq",
            model="openai/gpt-oss-120b",
            runtime_commit="abc123",
            registry_sha256="a" * 64,
            use_core=object(),
        )

    assert error.value.code == expected_code


def test_runner_requires_runtime_and_registry_identity():
    with pytest.raises(runner.GoldStarEvaluationRunError) as runtime_error:
        runner.run_synthetic_matched_pair(
            case_id="heldout-practical-trust-001",
            provider="groq",
            model="openai/gpt-oss-120b",
            runtime_commit="",
            registry_sha256="a" * 64,
            use_core=object(),
        )
    assert runtime_error.value.code == "runtime_commit_unavailable"

    with pytest.raises(runner.GoldStarEvaluationRunError) as registry_error:
        runner.run_synthetic_matched_pair(
            case_id="heldout-practical-trust-001",
            provider="groq",
            model="openai/gpt-oss-120b",
            runtime_commit="abc123",
            registry_sha256="not-a-digest",
            use_core=object(),
        )
    assert registry_error.value.code == "registry_digest_invalid"


def test_evaluation_route_requires_exact_mirror_explicit_enablement_and_secret():
    secret = "s" * 48
    assert runner.evaluation_route_authorized(
        service_id=runner.MIRROR_SERVICE_ID,
        enabled_flag="true",
        expected_secret=secret,
        supplied_secret=secret,
    )
    assert not runner.evaluation_route_authorized(
        service_id="srv-da98sm2jnfac73d2ki5g",
        enabled_flag="true",
        expected_secret=secret,
        supplied_secret=secret,
    )
    assert not runner.evaluation_route_authorized(
        service_id=runner.MIRROR_SERVICE_ID,
        enabled_flag="false",
        expected_secret=secret,
        supplied_secret=secret,
    )
    assert not runner.evaluation_route_authorized(
        service_id=runner.MIRROR_SERVICE_ID,
        enabled_flag="true",
        expected_secret="short",
        supplied_secret="short",
    )
    assert not runner.evaluation_route_authorized(
        service_id=runner.MIRROR_SERVICE_ID,
        enabled_flag="true",
        expected_secret=secret,
        supplied_secret="wrong-secret",
    )


def test_evaluation_payload_accepts_only_case_id_and_provider_model_pin():
    payload = {
        "case_id": "heldout-practical-trust-001",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }
    assert runner.validate_evaluation_request_payload(payload) == payload

    with pytest.raises(runner.GoldStarEvaluationRunError) as error:
        runner.validate_evaluation_request_payload({
            **payload,
            "query": "arbitrary caller-supplied text",
        })
    assert error.value.code == "invalid_evaluation_payload"

    with pytest.raises(runner.GoldStarEvaluationRunError):
        runner.validate_evaluation_request_payload({
            "case_id": "visitor-question",
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
        })


def test_main_endpoint_authenticates_before_reading_body_and_does_not_log_payload():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/internal/gold-star-evaluation-pair")')
    end = source.index('@app.post("/api/active-active-guide-capability")', start)
    route = source[start:end]

    assert route.index("evaluation_route_authorized") < route.index("request.stream()")
    assert "async for chunk in request.stream()" in route
    assert "await request.body()" not in route
    assert "X-Gold-Star-Evaluation-Key" in route
    assert "GOLD_STAR_EVALUATION_SECRET" in route
    assert "GOLD_STAR_EVALUATION_ENABLED" in route
    assert "request.json()" not in route
    assert "print(" not in route


def test_runner_allowlist_covers_the_complete_canonical_heldout_split():
    dataset = json.loads(
        (Path(__file__).resolve().parents[1] / "docs" / "qa" / "guide_learning_evaluation_set.json")
        .read_text(encoding="utf-8")
    )
    held_out_ids = {
        item["case_id"] for item in dataset["cases"]
        if isinstance(item, dict) and item.get("split") == "held_out"
    }
    assert runner.HELD_OUT_CASE_IDS == held_out_ids
    assert "heldout-community-rule-design-transfer-001" in runner.HELD_OUT_CASE_IDS


def test_community_rule_transfer_case_is_validly_allowlisted():
    payload = runner.validate_evaluation_request_payload({
        "case_id": "heldout-community-rule-design-transfer-001",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    })
    assert payload["case_id"] == "heldout-community-rule-design-transfer-001"
