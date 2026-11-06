"""Regression tests for governed General Guide Gold Standard exemplars."""

import gold_standard_exemplars as exemplars
import general_guide_composition as composition


def test_fully_user_approved_standard_is_available_as_a_structural_exemplar():
    selected = exemplars.select_exemplar("Why does human development matter?")
    assert selected is not None
    assert selected["benchmark_id"] == "general-guide-human-development-significance-2026-10-24"
    assert selected["status"] == "USER_APPROVED_GOLD_STANDARD"


def test_user_confirmed_reconstruction_variants_resolve_to_the_same_theme():
    variants = [
        "Why do I always end up doing everything for other people?",
        "How do I support someone without making them dependent on me?",
        "How can I help without taking away their independence?",
    ]
    for query in variants:
        selected = exemplars.select_exemplar(query)
        assert selected is not None, query
        assert selected["benchmark_id"] == "general-guide-original-gold-standard-02-2026-10-21"
        assert selected["status"] == "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT"


def test_generic_relationship_language_does_not_trigger_an_unrelated_exemplar():
    assert exemplars.select_exemplar(
        "What is the relationship between agency and circumstance?"
    ) is None
    assert exemplars.select_exemplar(
        "What is the relationship between trust and governance?"
    ) is None


def test_constitutional_reasoning_does_not_receive_an_unrelated_exemplar():
    assert exemplars.select_exemplar(
        "What is constitutional reasoning in the Archive's sense?"
    ) is None


def test_ambiguous_or_weak_queries_abstain():
    assert exemplars.select_exemplar("What is important?") is None
    assert exemplars.select_exemplar("Tell me about this.") is None


def test_guidance_contains_structure_but_never_answer_or_doorway():
    guidance, token = exemplars.build_exemplar_guidance(
        "How can I help without taking away their independence?"
    )
    assert token == "general-guide-original-gold-standard-02-2026-10-21"
    assert "structural cue only" in guidance
    assert "Do not copy the exemplar's answer" in guidance
    assert "https://geralddaquila.com/" not in guidance
    assert "Helping may be turning into taking over" not in guidance


def test_unrelated_question_falls_back_without_exemplar():
    guidance, token = exemplars.build_exemplar_guidance(
        "What is the speed of light in a vacuum?"
    )
    assert guidance == ""
    assert token == "none"


def test_registry_failure_is_nonfatal(monkeypatch):
    monkeypatch.setattr(exemplars, "_EXEMPLARS", [])
    assert exemplars.select_exemplar(
        "How can I help without taking away their independence?"
    ) is None


def test_composition_prompt_receives_structural_exemplar_guidance(monkeypatch):
    captured = {}

    def fake_guidance(query):
        assert query == "A question with a reviewed structural exemplar"
        return "STRUCTURAL EXEMPLAR CUE — DO NOT COPY CONTENT", "test-exemplar"

    def fake_provider(**kwargs):
        captured["messages"] = kwargs["messages"]
        return None

    monkeypatch.setattr(composition, "build_exemplar_guidance", fake_guidance)
    monkeypatch.setattr(composition, "route_with_model_bank", fake_provider)
    composition._COMPOSITION_CACHE.clear()

    composition.compose(
        use_core=object(),
        query="A question with a reviewed structural exemplar",
        context_data={},
    )

    assert "STRUCTURAL EXEMPLAR CUE — DO NOT COPY CONTENT" in captured["messages"][1]["content"]


def test_exemplar_identity_changes_the_composition_cache_key():
    first = composition._composition_cache_key(
        "same question", "", "explanatory|gold_standard_exemplar:exemplar-a", []
    )
    second = composition._composition_cache_key(
        "same question", "", "explanatory|gold_standard_exemplar:exemplar-b", []
    )
    assert first != second


def test_exact_low_token_question_uses_its_structural_exemplar():
    query = "What does accountability really mean?"
    selected = exemplars.select_exemplar(query)
    assert selected is not None
    assert selected["benchmark_id"] == "general-guide-original-gold-standard-05-2026-10-21"
    assert selected["status"] == "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT"

    guidance, token = exemplars.build_exemplar_guidance(query)
    assert token == selected["benchmark_id"]
    assert "structural cue only" in guidance
    assert "Accountability means being answerable for what you did" not in guidance


def test_every_reviewed_registry_record_is_loaded_and_unreviewed_records_are_excluded():
    import json

    payload = json.loads(exemplars._REGISTRY_PATH.read_text(encoding="utf-8"))
    allowed = exemplars._ALLOWED_STATUSES
    reviewed = {
        record["benchmark_id"]
        for record in payload["records"]
        if record.get("subsystem") == "general-purpose-guide"
        and record.get("status") in allowed
        and record.get("query")
        and exemplars._response_for_record(record)
    }
    approved = {
        record["benchmark_id"]
        for record in payload["records"]
        if record.get("subsystem") == "general-purpose-guide"
        and record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and record.get("query")
        and exemplars._response_for_record(record)
    }
    loaded = {record["id"] for record in exemplars._EXEMPLARS}

    assert reviewed == loaded
    assert approved
    assert approved <= loaded
    assert all(record["status"] in allowed for record in exemplars._EXEMPLARS)

