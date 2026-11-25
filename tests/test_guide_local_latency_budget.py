"""Regression tests for the Guide-local provider latency budget."""

import provider_bank


def test_guide_provider_call_timeout_is_bounded():
    assert provider_bank._provider_call_timeout(
        "general_guide_composition",
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
    ) == provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS


def test_guide_fast_failure_budget_is_narrow_and_bounded():
    # The current Guide budget reserves a 24-second request deadline, a
    # six-second integrity-repair reserve, and an 18-second bounded provider
    # arbitration window for one primary plus a bounded fallback set.
    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == 18.0
    assert provider_bank.GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES == 6


def test_guide_timeout_does_not_change_hrn_provider_timeout():
    assert provider_bank._provider_call_timeout(
        "hrn_relational",
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
    ) == provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS


def test_generic_operations_keep_existing_timeout_policy():
    assert provider_bank._provider_call_timeout(
        "generic",
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
    ) is None
