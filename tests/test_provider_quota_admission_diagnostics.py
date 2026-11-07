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
