"""Regression tests for practical stewardship recovery when route providers fail."""
import main as use_main


QUERY = "How can a community practice stewardship in its everyday decisions and responsibilities?"


def test_practical_stewardship_route_fallback_survives_provider_exhaustion(monkeypatch):
    monkeypatch.setattr(use_main, "route_with_model_bank", lambda **kwargs: None)
    route = use_main._guide_capability_route(QUERY)
    assert route["route"] == "guide"
    assert route["mode"] == "direct"
    assert route["source"] == "deterministic-practical-stewardship-fallback"


def test_practical_stewardship_recovery_returns_substantive_answer_without_archive_claim(monkeypatch):
    monkeypatch.setattr(use_main.use_core, "context_blocks_to_documents", lambda _text: [])
    result = use_main._basic_inquiry_round1_deterministic_response(
        QUERY, {}, {"context_blocks": ""}, recommendation_available=False
    )
    answer = result["response"].casefold()
    assert result["provider"] == "bounded_practical_stewardship_recovery"
    assert "people who rely on it" in answer
    assert "clear criteria" in answer
    assert "review the outcome" in answer
    assert "general practical suggestions" in answer
    assert "sufficiently direct archive resource" in answer
    assert result["doorway_title"] == ""


def test_explicit_formation_entry_is_not_overridden():
    query = "How do I enter the Stewardship Formation pathway?"
    assert not use_main._is_practical_stewardship_question(query)
    result = use_main._guide_route_fallback(query)
    assert result["route"] != "formation"  # fallback never fabricates a Formation entry
    assert use_main._explicit_formation_entry_route(query)["route"] == "formation"


def test_funding_priority_question_keeps_its_own_recovery():
    query = "How should a community decide which of two competing priorities deserves funding when neither can be fully supported?"
    assert not use_main._is_practical_stewardship_question(query)
    result = use_main._basic_inquiry_round1_deterministic_response(query, {}, {"context_blocks": ""})
    assert result["provider"] == "bounded_funding_priority_recovery"
