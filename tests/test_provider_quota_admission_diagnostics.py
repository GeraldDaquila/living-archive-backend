"""Regression tests for precise, non-secret provider quota admission reasons."""
import pytest

import provider_quota_control as quota


def test_rpm_budget_rejection_exposes_specific_reason(monkeypatch):
    quota._reset_for_tests()
    monkeypatch.setenv("USE_QUOTA_GROQ_RPM", "1")
    first = quota.reserve("groq", "model-a", [{"role": "user", "content": "x"}], 1)
    first.release()
    try:
        with pytest.raises(quota.QuotaAdmissionDenied) as caught:
            quota.reserve("groq", "model-b", [{"role": "user", "content": "x"}], 1)
        assert caught.value.reason == "rpm_budget_exhausted"
        assert caught.value.retry_after > 0
    finally:
        quota._reset_for_tests()


def test_provider_concurrency_rejection_exposes_specific_reason(monkeypatch):
    quota._reset_for_tests()
    monkeypatch.setenv("USE_QUOTA_MAX_INFLIGHT_PROVIDER", "1")
    first = quota.reserve("groq", "model-a", [{"role": "user", "content": "x"}], 1)
    try:
        with pytest.raises(quota.QuotaAdmissionDenied) as caught:
            quota.reserve("groq", "model-b", [{"role": "user", "content": "x"}], 1)
        assert caught.value.reason == "provider_concurrency_cap"
    finally:
        first.release()
        quota._reset_for_tests()

import pytest

import provider_quota_control as quota


def test_rpm_budget_rejection_exposes_specific_reason(monkeypatch):
    quota._reset_for_tests()
    monkeypatch.setenv("USE_QUOTA_GROQ_RPM", "1")
    first = quota.reserve("groq", "model-a", [{"role": "user", "content": "x"}], 1)
    first.release()
    try:
        with pytest.raises(quota.QuotaAdmissionDenied) as caught:
            quota.reserve("groq", "model-b", [{"role": "user", "content": "x"}], 1)
        assert caught.value.reason == "rpm_budget_exhausted"
        assert caught.value.retry_after > 0
    finally:
        quota._reset_for_tests()


def test_provider_concurrency_rejection_exposes_specific_reason(monkeypatch):
    quota._reset_for_tests()
    monkeypatch.setenv("USE_QUOTA_MAX_INFLIGHT_PROVIDER", "1")
    first = quota.reserve("groq", "model-a", [{"role": "user", "content": "x"}], 1)
    try:
        with pytest.raises(quota.QuotaAdmissionDenied) as caught:
            quota.reserve("groq", "model-b", [{"role": "user", "content": "x"}], 1)
        assert caught.value.reason == "provider_concurrency_cap"
    finally:
        first.release()
        quota._reset_for_tests()

def test_tpm_budget_denial_exposes_limit_and_request_estimate(monkeypatch):
    quota._reset_for_tests()
    monkeypatch.setenv("USE_QUOTA_GROQ_TPM", "1")
    try:
        with pytest.raises(quota.QuotaAdmissionDenied) as caught:
            quota.reserve("groq", "model-a", [{"role": "user", "content": "x"}], 32)
        assert caught.value.reason == "tpm_budget_exhausted"
        assert caught.value.budget_kind == "tpm"
        assert caught.value.budget_limit == 1
        assert caught.value.request_cost > caught.value.budget_limit
        assert caught.value.budget_period_seconds == 60.0
    finally:
        quota._reset_for_tests()


from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import provider_bank
from provider_quota_control import QuotaAdmissionDenied


def test_quota_admission_denial_logs_reason_without_request_content():
    denial = QuotaAdmissionDenied(
        "groq", "qwen/qwen3.8-27b", "tpm_budget_exhausted", 12.5,
        budget_kind="tpm", budget_limit=1000, request_cost=1800,
        budget_period_seconds=60.0,
    )
    output = StringIO()
    with patch.object(provider_bank, "reserve_provider_call", side_effect=denial):
        with redirect_stdout(output):
            with pytest.raises(QuotaAdmissionDenied):
                provider_bank._quota_guarded_call(
                    object(),
                    {"provider": "groq", "model": "qwen/qwen3.8-27b"},
                    [{"role": "user", "content": "PRIVATE VISITOR QUESTION"}],
                    900,
                    operation="general_guide_composition",
                )
    logged = output.getvalue()
    assert "reason=tpm_budget_exhausted" in logged
    assert "budget_kind=tpm" in logged
    assert "budget_limit=1000" in logged
    assert "request_cost=1800" in logged
    assert "retry_after_seconds=12.50" in logged
    assert "PRIVATE VISITOR QUESTION" not in logged


def test_quota_admission_diagnostic_does_not_expose_exception_text():
    denial = QuotaAdmissionDenied(
        "mistral", "mistral-small-latest", "rpm_budget_exhausted", 4.0
    )
    output = StringIO()
    with patch.object(provider_bank, "reserve_provider_call", side_effect=denial):
        with redirect_stdout(output):
            with pytest.raises(QuotaAdmissionDenied):
                provider_bank._quota_guarded_call(
                    object(),
                    {"provider": "mistral", "model": "mistral-small-latest"},
                    [{"role": "user", "content": "secret"}],
                    900,
                    operation="general_guide_composition",
                )
    logged = output.getvalue()
    assert "reason=rpm_budget_exhausted" in logged
    assert "secret" not in logged
    assert "provider admission denied:" not in logged
