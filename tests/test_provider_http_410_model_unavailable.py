import time

import pytest

import provider_bank
from provider_resilience import new_state


class _GoneModelError(Exception):
    category = "provider_failure"
    retry_after = None

    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code} model endpoint unavailable")


@pytest.mark.parametrize("status_code", [404, 410])
def test_gone_model_status_uses_one_hour_model_only_quarantine(monkeypatch, status_code):
    model = "google/gemma-4-31b-it"
    state = new_state("nvidia", model)
    monkeypatch.setattr(provider_bank, "_state", lambda provider, candidate: state)

    category = provider_bank._failure(
        _GoneModelError(status_code),
        "nvidia",
        model,
        operation="general_guide_composition",
    )

    assert category == "model_unavailable"
    assert state["category"] == "model_unavailable"
    assert state["quarantine_until"] >= time.time() + 3590
    assert state["cooldown_until"] == 0.0
