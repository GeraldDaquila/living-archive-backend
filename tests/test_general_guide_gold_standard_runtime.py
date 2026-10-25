import json
from pathlib import Path

import pytest

from general_guide_gold_standards import resolve_exact_gold_standard, load_approved_standards

ROOT = Path(__file__).resolve().parents[1]


def test_user_approved_water_answer_is_enforced_exactly():
    result = resolve_exact_gold_standard("What is the boiling point of water at sea level?")
    assert result is not None
    assert result["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert result["expected_response"] == (
        "At sea level, water boils at 100°C (212°F) under standard atmospheric pressure. "
        "As altitude increases and air pressure decreases, water boils at a lower temperature.\n\n"
        "The key point is that boiling depends on pressure, not just temperature."
    )


def test_frozen_stewardship_answer_is_enforced_exactly():
    result = resolve_exact_gold_standard("Explain stewardship, but do not send me to another page yet.")
    assert result is not None
    assert result["status"] == "FROZEN_REFERENCE_ONLY"
    assert len(result["expected_response"].split("\n\n")) == 3
    assert "does not mean controlling everything" in result["expected_response"]


def test_matching_is_case_and_whitespace_insensitive_but_not_fuzzy():
    assert resolve_exact_gold_standard("  WHAT IS THE BOILING POINT OF WATER AT SEA LEVEL?  ") is not None
    assert resolve_exact_gold_standard("What is the boiling point of water?") is None


def test_recovered_historical_response_is_not_runtime_authority():
    result = resolve_exact_gold_standard(
        "What does stewardship look like when people disagree about what is worth protecting?"
    )
    assert result is None


def test_registry_conflicts_are_rejected(monkeypatch, tmp_path):
    import general_guide_gold_standards as standards
    registry = {
        "records": [
            {"status": "USER_APPROVED_GOLD_STANDARD", "query": "Same question?", "expected_response": "Answer A"},
            {"status": "FROZEN_REFERENCE_ONLY", "query": "same   question?", "expected_response": "Answer B"},
        ]
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(standards, "_REGISTRY_PATH", path)
    with pytest.raises(ValueError, match="Conflicting approved"):
        standards.load_approved_standards()


def test_general_composition_returns_registered_answer_before_provider_call(monkeypatch):
    import general_guide_composition as composition

    def provider_must_not_be_called(**kwargs):
        raise AssertionError("Provider bank must not replace an exact approved answer.")

    monkeypatch.setattr(composition, "route_with_model_bank", provider_must_not_be_called)
    result = composition.compose(
        use_core=object(),
        query="What is the boiling point of water at sea level?",
        context_data={},
    )
    assert result["response"] == resolve_exact_gold_standard(
        "What is the boiling point of water at sea level?"
    )["expected_response"]
    assert result["provider"] == "gold_standard_registry"
