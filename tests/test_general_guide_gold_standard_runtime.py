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
    assert result["doorway_title"] == ""
    assert result["doorway_url"] == ""


def test_registered_doorway_is_preserved_when_no_handoff_was_not_requested():
    result = resolve_exact_gold_standard("What is the significance of human development?")
    assert result is not None
    assert result["doorway_title"] == "The First Institution: Why Human Development Begins at Home"
    assert result["doorway_url"] == "https://geralddaquila.com/2025/06/17/the-first-institution-why-human-development-begins-at-home/"


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
    assert result["doorway_title"] == ""


def test_cosmology_question_is_not_replaced_by_an_exact_benchmark_answer(monkeypatch):
    import general_guide_composition as composition

    query = "What is cosmology, and why does it matter to how people live?"
    provider_response = (
        "Cosmology is an account of how the world is understood and how its parts fit together. "
        "It matters because a person's picture of reality shapes what they notice, what they value, "
        "and what they believe is possible. For example, if people see themselves as separate from "
        "one another, they may treat shared problems as someone else's concern; seeing relationships "
        "as interconnected can make mutual consequences easier to recognize."
    )

    def provider(**kwargs):
        return {
            "parsed": {
                "response": provider_response,
                "doorway_title": "The Worldview of a Conscious Human",
                "response_shape": "explanatory",
            },
            "provider": "test-provider",
            "model": "test-model",
        }

    monkeypatch.setattr(composition, "route_with_model_bank", provider)
    result = composition.compose(
        use_core=object(),
        query=query,
        context_data={},
    )

    assert resolve_exact_gold_standard(query) is None
    assert result["provider"] == "test-provider"
    assert result["response"] == provider_response
    assert "shapes what they notice" in result["response"]
    assert "The Worldview of a Conscious Human" == result["doorway_title"]

def test_main_final_payload_boundary_reapplies_exact_standard_after_rewrites():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    resolver_call = '_final_gold_standard = _resolve_exact_guide_gold_standard(query)'
    payload_marker = '    payload = {\n        "ok": True,\n        "version": APP_VERSION,'
    assert resolver_call in main_source
    assert payload_marker in main_source
    resolver_position = main_source.index(resolver_call)
    payload_position = main_source.index(payload_marker, resolver_position)
    final_contract_position = main_source.index(
        'general_guide_composition.enforce_response_contracts(query, response)'
    )
    assert final_contract_position < resolver_position < payload_position
    assert 'response = _final_gold_standard["expected_response"]' in main_source
    final_block = main_source[resolver_position:payload_position]
    assert '_gold_forbids_doorway = bool(_final_gold_standard.get("forbids_doorway"))' in final_block
    assert 'elif _gold_forbids_doorway:' in final_block
    assert 'Otherwise retain the independently selected, relevance-checked' in final_block


def test_water_gold_standard_keeps_general_knowledge_provenance():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert (
        '_final_gold_standard.get("benchmark_id") == '
        '"general-guide-water-boiling-point-general-knowledge-gold-standard-2026-10-24"'
    ) in main_source
    assert "GS-GENERAL-BOILING-POINT-WATER-001" not in main_source


def test_frozen_core_blob_is_not_modified_by_runtime_integration():
    # Guard the protected production core's reviewed identity in CI.
    # The expected SHA is the known unchanged blob for this release line.
    import subprocess

    result = subprocess.run(
        ["git", "hash-object", "use_core.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "fb3208a8d287f16562ffd640d89f65d5e8d18607"



def test_first_principles_gold_standard_matches_straight_and_curly_apostrophes(monkeypatch):
    import general_guide_composition as composition

    curly = "What are first principles, and what are the Living Archive’s first principles?"
    straight = "What are first principles, and what are the Living Archive's first principles?"
    expected = resolve_exact_gold_standard(curly)
    assert expected is not None
    assert resolve_exact_gold_standard(straight)["expected_response"] == expected["expected_response"]

    def provider_must_not_be_called(**kwargs):
        raise AssertionError("Provider bank must not replace the approved First Principles answer.")

    monkeypatch.setattr(composition, "route_with_model_bank", provider_must_not_be_called)
    result = composition.compose(use_core=object(), query=straight, context_data={})
    assert result["provider"] == "gold_standard_registry"
    assert result["response"] == expected["expected_response"]
    assert result["doorway_title"] == "First Principles"
    assert result["doorway_url"] == "https://geralddaquila.com/first-principles/"


def test_first_principles_gold_standard_names_all_six_published_principles():
    result = resolve_exact_gold_standard(
        "What are first principles, and what are the Living Archive’s first principles?"
    )
    assert result is not None
    answer = result["expected_response"]
    assert len(answer.split("\n\n")) == 3
    for principle in (
        "reality is intelligible",
        "human beings participate in reality",
        "understanding develops",
        "complexity deserves integration rather than reduction",
        "stewardship follows understanding",
        "every generation inherits unfinished questions",
    ):
        assert principle in answer
    assert "not unquestionable doctrines" in answer
    assert result["doorway_title"] == "First Principles"
    assert result["doorway_url"] == "https://geralddaquila.com/first-principles/"



def test_continuous_learning_contract_is_explicit_and_does_not_claim_implementation():
    registry = json.loads(
        (ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8")
    )
    contract = registry["learning_contract"]

    assert contract["contract_id"] == "living-archive-guide-continuous-learning-loop"
    assert contract["contract_version"] == "1.0.0"
    assert contract["status"] == "SPECIFIED_NOT_YET_IMPLEMENTED"
    assert any("questions not used during calibration" in item for item in contract["governing_principles"])
    assert any("does not train a model" in item for item in contract["data_and_authority_boundaries"])
    assert "human approval" in contract["learning_cycle"][-2]["requirement"]
    assert any("held-out question suite" in item.lower() for item in contract["acceptance_gates"])
    assert "current exact-match registry" in contract["current_capability_boundary"]
    assert [stage["stage"] for stage in contract["rollout_stages"]] == [
        "1_contract_and_baseline",
        "2_shadow_evaluation",
        "3_reviewed_adaptation",
        "4_guarded_promotion",
        "5_continuous_monitoring",
    ]
