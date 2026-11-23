"""Request-local isolation contracts for Gold Star matched-pair evaluation."""

import pytest

import general_guide_composition as composition
import provider_bank
from gold_star_evaluation_context import (
    current_evaluation_context,
    evaluation_context,
)
from provider_bank import _filter_evaluation_candidate_pool


def test_evaluation_context_is_nested_and_restored():
    assert current_evaluation_context() is None
    with evaluation_context(arm="control", provider="groq", model="openai/gpt-oss-120b"):
        outer = current_evaluation_context()
        assert outer.arm == "control"
        with evaluation_context(arm="treatment", provider="groq", model="openai/gpt-oss-120b"):
            assert current_evaluation_context().arm == "treatment"
        assert current_evaluation_context() is outer
    assert current_evaluation_context() is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"arm": "unknown", "provider": "groq", "model": "model-x"},
        {"arm": "control", "provider": "", "model": "model-x"},
        {"arm": "treatment", "provider": "groq", "model": ""},
    ],
)
def test_evaluation_context_rejects_incomplete_or_unknown_pins(kwargs):
    with pytest.raises(ValueError):
        with evaluation_context(**kwargs):
            pass


def test_provider_candidate_filter_keeps_only_exact_pinned_pair():
    candidates = [
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
        {"provider": "groq", "model": "openai/gpt-oss-20b"},
        {"provider": "workers_ai", "model": "@cf/google/gemma-4-26b-a4b-it"},
    ]
    with evaluation_context(
        arm="treatment", provider="groq", model="openai/gpt-oss-120b"
    ) as pin:
        selected = _filter_evaluation_candidate_pool(candidates, pin)
    assert selected == [candidates[0]]


def test_pinned_route_never_attempts_active_active_delegation(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("evaluation routing must remain local")

    monkeypatch.setattr(provider_bank, "_active_active_primary_assignment", forbidden)
    monkeypatch.setattr(provider_bank, "_active_active_delegate", forbidden)
    monkeypatch.setattr(provider_bank, "_active_active_role", lambda: "primary")
    monkeypatch.setattr(provider_bank, "refresh_server_capacity_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "select", lambda *_args, **_kwargs: [])

    with evaluation_context(
        arm="control", provider="groq", model="openai/gpt-oss-120b"
    ):
        result = provider_bank.route(
            use_core=object(),
            messages=[{"role": "user", "content": "synthetic evaluation"}],
            max_tokens=100,
            parse=lambda value: value,
            operation="general_guide_composition",
        )

    assert result is None


def test_control_and_treatment_each_generate_without_composition_cache(monkeypatch):
    route_calls = []
    contribution_calls = []
    candidate = {
        "benchmark_id": "approved-structural-lesson-eval-001",
        "score": 0.91,
        "exact": False,
        "query": "How should evidence and accountability be related?",
        "known_theme": "Trace responsibility through evidence and consequences.",
        "reasoning_family": "evidence_to_accountability",
        "discipline": "Connect claims to evidence, then trace who owns consequences.",
        "abstention_boundary": "Do not infer responsibility where the evidence does not establish it.",
    }
    contribution = {
        "benchmark_id": candidate["benchmark_id"],
        "score": candidate["score"],
        "authority_mode": "structural_guidance_only",
        "candidates": [candidate],
    }

    def fake_contribution(question):
        contribution_calls.append(question)
        return contribution

    def fake_route(**kwargs):
        route_calls.append(kwargs)
        return {"parsed": {"response": "A direct, relevant answer."}}

    monkeypatch.setattr(
        composition, "_gold_star_active_quality_contribution", fake_contribution
    )
    monkeypatch.setattr(
        composition, "_registered_exact_gold_standard", lambda _question: None
    )
    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)

    question = (
        "How can a local clinic explain who is accountable for delayed test results?"
    )
    for arm in ("control", "treatment"):
        with evaluation_context(
            arm=arm, provider="groq", model="openai/gpt-oss-120b"
        ):
            result = composition.compose(
                use_core=object(),
                query=question,
                context_data={},
            )
        assert result is not None

    assert len(route_calls) == 2
    assert len(contribution_calls) == 1
    control_system = next(
        item["content"]
        for item in route_calls[0]["messages"]
        if item["role"] == "system"
    )
    treatment_system = next(
        item["content"]
        for item in route_calls[1]["messages"]
        if item["role"] == "system"
    )
    assert candidate["benchmark_id"] not in control_system
    assert candidate["benchmark_id"] in treatment_system
    assert candidate["discipline"] not in control_system
    assert candidate["discipline"] in treatment_system
