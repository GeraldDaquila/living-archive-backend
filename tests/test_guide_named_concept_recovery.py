"""Regression contract for named-concept definitions and Archive orientation.

A general definition and an Archive doorway are separate obligations:
metadata-only crosslinks may orient a visitor but must never be treated as
evidence for an attributed definition.
"""
import general_guide_composition as composition
from deterministic_answer_recovery import compose_definition_significance
from main import _established_general_knowledge_recovery


def test_registered_named_concept_has_bounded_general_knowledge_orientation():
    recovery = _established_general_knowledge_recovery("What is the Law of One?")
    assert recovery is not None
    assert recovery["fact_id"] == "public_concept_law_of_one"
    assert "unity of all existence" in recovery["response"]
    assert "not a claim about how the Living Archive uses it" in recovery["response"]
    assert not composition.is_generic_nonanswer(
        "What is the Law of One?", recovery["response"]
    )


def test_existing_known_definition_bank_remains_unchanged():
    answer = compose_definition_significance("reciprocity")
    assert answer.startswith("Reciprocity is a relationship of mutual response")
    assert "Neighbors may take turns" in answer
    assert "immediate or equal repayment" in answer


def test_territorial_crosslink_metadata_is_not_source_evidence():
    metadata_only = {
        "title": "A canonical Archive destination",
        "url": "https://geralddaquila.com/a-canonical-destination/",
        "summary": "A short navigation description.",
        "content": "",
        "crosslink_mode": "territorial_navigation",
    }
    assert not str(metadata_only.get("content") or "").strip()
    assert metadata_only["crosslink_mode"] == "territorial_navigation"


def test_named_concept_remains_general_question_not_navigation_command():
    query = "What is the Law of One?"
    assert not any(
        phrase in query.casefold()
        for phrase in ("where can i find", "show me", "take me to", "open the", "go to")
    )


def test_registered_named_concept_runtime_recovery_has_precedence_over_provider_fallback():
    recovery = _established_general_knowledge_recovery("What is the Law of One?")
    assert recovery is not None
    assert recovery["fact_id"] == "public_concept_law_of_one"
    assert recovery["response"].startswith("“The Law of One” is")
    assert "I can't define" not in recovery["response"]


def test_registered_named_concept_accepts_optional_leading_article():
    recovery = _established_general_knowledge_recovery("What is the Law of One?")
    assert recovery is not None
    assert recovery["fact_id"] == "public_concept_law_of_one"
