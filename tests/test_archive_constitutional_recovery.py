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


def test_provider_success_cannot_bypass_constitutional_answer_contract(monkeypatch):
    documents = [
        {
            "title": "Living Archive Constitutional Register",
            "url": "https://geralddaquila.com/constitutional-register/",
            "content": (
                "The Constitutional Register records the Archive's constitutional "
                "architecture and governing relationships. Recovery precedes translation; "
                "later interpretation must remain distinguishable from established material."
            ),
        }
    ]
    monkeypatch.setattr(
        guide, "_documents_from_context", lambda use_core, context_data: documents
    )
    monkeypatch.setattr(
        guide,
        "route_with_model_bank",
        lambda **kwargs: {
            "parsed": {
                "response": (
                    "Constitutional reasoning is an important way to understand the Archive. "
                    "It can help readers think about principles and decisions.\\n\\n"
                    "The Register is a useful place to begin.\\n\\n"
                    "Readers should distinguish facts from opinions."
                ),
                "doorway_title": "",
                "response_shape": "explanatory",
            },
            "provider": "test-provider",
            "model": "test-model",
            "preference_order": ["test-provider:test-model"],
        },
    )
    guide._COMPOSITION_CACHE.clear()

    result = guide.compose(
        use_core=None,
        query="What is constitutional reasoning in the Archive's sense?",
        context_data={},
    )

    assert result is not None
    assert result["provider"] == "bounded_archive_constitutional_recovery"
    assert "governing relationships" in result["response"].casefold()
    assert "recovery before translation" in result["response"].casefold()
    assert "recovered constitutional architecture" in result["response"].casefold()
    assert "later interpretation" in result["response"].casefold()
    assert result["doorway_title"] == "Living Archive Constitutional Register"
    assert result["doorway_url"] == "https://geralddaquila.com/constitutional-register/"


def test_constitutional_answer_contract_rejects_parseable_but_incomplete_answer():
    assert not guide._archive_constitutional_response_satisfies_contract(
        "Constitutional reasoning is important. It helps readers understand the Archive."
    )
    assert guide._archive_constitutional_response_satisfies_contract(
        "Constitutional reasoning recovers governing relationships and constitutional architecture. "
        "It preserves recovery before translation and distinguishes later interpretation."
    )
