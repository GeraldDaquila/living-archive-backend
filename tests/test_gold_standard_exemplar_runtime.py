"""Contract tests for runtime General Guide exemplar selection."""
import gold_standard_exemplars as exemplars


def test_user_confirmed_helping_example_is_available_as_structure():
    selected = exemplars.select_exemplar(
        "How can I tell if I am helping too much and taking over?"
    )
    assert selected is not None
    assert selected["benchmark_id"] == "general-guide-original-gold-standard-02-2026-10-21"
    assert selected["status"] == "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT"


def test_exemplar_guidance_explicitly_forbids_copying_and_doorway_transfer():
    guidance, token = exemplars.build_exemplar_guidance(
        "How can I tell when helping has turned into taking over?"
    )
    assert token == "general-guide-original-gold-standard-02-2026-10-21"
    assert "structural cue only" in guidance
    assert "Do not copy claims, examples, or any destination" in guidance


def test_unrelated_question_falls_back_without_exemplar():
    guidance, token = exemplars.build_exemplar_guidance(
        "What is the boiling point of water at sea level?"
    )
    assert guidance == ""
    assert token == "none"


def test_registry_failure_is_nonfatal(monkeypatch):
    monkeypatch.setattr(exemplars, "_EXEMPLARS", [])
    assert exemplars.select_exemplar("How can I tell when helping has turned into taking over?") is None
