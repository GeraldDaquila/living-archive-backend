"""Regression tests for evidence-gated Archive constitutional recovery."""

import general_guide_composition as guide
from deterministic_answer_recovery import compose_recovery


def test_archive_definition_recovery_does_not_capture_a_concept_in_archive_context():
    archive_definition = compose_recovery(
        "What is the Living Archive, and what is it not?"
    )
    assert "The Living Archive is a public knowledge commons" in archive_definition
    assert "It is not a chatbot" in archive_definition

    constitutional_question = compose_recovery(
        "What is constitutional reasoning in the Archive's sense?"
    )
    assert "The Living Archive is a public knowledge commons" not in constitutional_question
    assert "It is not a chatbot" not in constitutional_question
    assert "Constitutional reasoning in the Archive's sense" in constitutional_question


def test_provider_exhaustion_uses_verified_constitutional_register_evidence(monkeypatch):
    documents = [
        {
            "title": "Living Archive Constitutional Register",
            "url": "https://geralddaquila.com/constitutional-register/",
            "content": (
                "The Constitutional Register records the Archive's constitutional "
                "architecture and governing relationships. Recovery precedes translation; "
                "later interpretation must remain distinguishable from established material."
            ),
        },
        {
            "title": "Document Types of the Living Archive",
            "url": "https://geralddaquila.com/document-types/",
            "content": "Document types distinguish different roles within the Archive.",
        },
    ]
    monkeypatch.setattr(
        guide, "_documents_from_context", lambda use_core, context_data: documents
    )
    monkeypatch.setattr(guide, "route_with_model_bank", lambda **kwargs: None)
    guide._COMPOSITION_CACHE.clear()

    result = guide.compose(
        use_core=None,
        query="What is constitutional reasoning in the Archive's sense?",
        context_data={},
    )

    assert result is not None
    assert result["provider"] == "bounded_archive_constitutional_recovery"
    assert result["doorway_title"] == "Living Archive Constitutional Register"
    assert result["doorway_url"] == "https://geralddaquila.com/constitutional-register/"
    response = result["response"]
    assert len(response.split("\n\n")) == 3
    assert "constitutional reasoning" in response.casefold()
    assert "governing relationships" in response.casefold()
    assert "recovery before translation" in response.casefold()
    assert "recovered constitutional architecture" in response.casefold()
    assert "later interpretation" in response.casefold()


def test_constitutional_recovery_fails_closed_without_constitutional_register_evidence(monkeypatch):
    documents = [
        {
            "title": "General Archive Introduction",
            "url": "https://geralddaquila.com/introduction/",
            "content": "A general overview of the Archive's public purpose.",
        }
    ]
    monkeypatch.setattr(
        guide, "_documents_from_context", lambda use_core, context_data: documents
    )
    monkeypatch.setattr(guide, "route_with_model_bank", lambda **kwargs: None)
    guide._COMPOSITION_CACHE.clear()

    result = guide.compose(
        use_core=None,
        query="What is constitutional reasoning in the Archive's sense?",
        context_data={},
    )

    assert result is None



def test_final_response_contract_fails_closed_without_canonical_evidence():
    question = "What is constitutional reasoning in the Archive's sense?"
    weak_candidate = (
        "Constitutional reasoning is a way of thinking about rules and principles. "
        "It can help people understand a framework.\n\n"
        "For example, a group can discuss its values before making a decision.\n\n"
        "This can help guide later choices and interpretations."
    )
    import pytest

    with pytest.raises(RuntimeError, match="evidence-grounded recovery was not supplied"):
        guide.enforce_response_contracts(question, weak_candidate)


def test_final_response_contract_preserves_a_valid_constitutional_explanation():
    question = "What is constitutional reasoning in the Archive's sense?"
    strong_candidate = (
        "Constitutional reasoning recovers the governing relationships in the Archive's constitutional architecture. "
        "It distinguishes established source material from later interpretation.\n\n"
        "Recovery before translation means identifying what canonical sources establish before explaining them.\n\n"
        "Recovered constitutional architecture remains distinct from later interpretation."
    )
    assert guide.enforce_response_contracts(question, strong_candidate) == strong_candidate
