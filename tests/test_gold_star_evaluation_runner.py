"""Contracts for synthetic-only Gold Star paired generation."""

import pytest

import gold_star_evaluation_runner as runner
from gold_star_evaluation_context import current_evaluation_context


def _fake_compose_factory(*, mismatch=False, rewrite=False, no_treatment_guidance=False):
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
        }
        return {
            "provider": "other-provider" if mismatch else context.provider,
            "model": context.model,
            "response": f"Synthetic {arm} output.",
            "doorway_title": "",
            "doorway_url": "",
            "_gold_star_evaluation_response_unchanged": not rewrite,
            "_gold_star_adjudication_trace": trace,
        }

    return fake_compose, calls


def test_runner_generates_blinded_fresh_pair_from_fixed_heldout_case(monkeypatch):
    fake_compose, calls = _fake_compose_factory()
    monkeypatch.setattr(runner._composition, "compose", fake_compose)

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
    assert [arm for arm, _query in calls] == ["control", "treatment"]
    assert calls[0][1] == calls[1][1]
    assert current_evaluation_context() is None

    artifacts = result["blind_artifacts"]
    assert len(artifacts) == 2
    assert {item["output"] for item in artifacts} == {
        "Synthetic control output.",
        "Synthetic treatment output.",
    }
    assert all("arm" not in item for item in artifacts)
    assert artifacts[0]["artifact_ref"] != artifacts[1]["artifact_ref"]

    manifest = result["operator_manifest"]
    assert manifest["case_id"] == "heldout-practical-trust-001"
    assert manifest["case_family"] == "practical_application"
    assert manifest["provider"] == "groq"
    assert manifest["model"] == "openai/gpt-oss-120b"
    assert manifest["control"]["adaptation_enabled"] is False
    assert manifest["treatment"]["adaptation_enabled"] is True
    assert manifest["control"]["output_artifact_ref"] != manifest["treatment"]["output_artifact_ref"]
    assert manifest["treatment_guidance_candidate_count"] == 1
    assert manifest["treatment_guidance_exposure"] == "included_in_provider_prompt"
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
        service_id="primary-service-id",
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
