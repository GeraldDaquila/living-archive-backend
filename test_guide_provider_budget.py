from pathlib import Path


def test_general_guide_provider_arbitration_preserves_recovery_budget():
    source = Path("provider_bank.py").read_text(encoding="utf-8")
    assert "GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS = 8.0" in source
    assert "GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES = 2" in source
    assert (
        "if candidate_timeout <= 0.0 or elapsed + candidate_timeout > fast_failure_window:"
        in source
    )


def test_guide_request_budget_retains_one_absolute_deadline():
    source = Path("guide_request_budget.py").read_text(encoding="utf-8")
    assert "REQUEST_BUDGET_SECONDS = 24.0" in source
    assert "def remaining_seconds(" in source
    assert "def bounded_provider_timeout(" in source


def test_general_guide_success_outcome_includes_fresh_shadow_metrics():
    source = Path("provider_bank.py").read_text(encoding="utf-8")
    assert 'outcome=success, elapsed_seconds=' in source
    assert '_predictive_shadow_metrics(state, _provider_call_timeout(operation, item))' in source
