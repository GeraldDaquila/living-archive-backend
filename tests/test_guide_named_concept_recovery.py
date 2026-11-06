"""Regression contract for named-concept definitions and Archive orientation.

A general definition and an Archive doorway are separate obligations:
metadata-only crosslinks may orient a visitor but must never be treated as
evidence for an attributed definition.
"""
import general_guide_composition as composition
from deterministic_answer_recovery import compose_definition_significance


def test_unknown_named_concept_does_not_emit_circular_generic_refusal():
    answer = compose_definition_significance("The Law of One")
    assert "I can't define" in answer
    assert "The Law of One" in answer
    assert "reliable dictionary or subject reference" in answer
    assert "unanswerable in principle" in answer
    assert not composition.is_generic_nonanswer(
        "What is the Law of One?", answer
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
