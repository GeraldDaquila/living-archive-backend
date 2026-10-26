"""Provider-exhaustion definition recovery contract tests."""
from pathlib import Path

import general_guide_composition as composition
from deterministic_answer_recovery import compose_recovery


ROOT = Path(__file__).resolve().parents[1]


def test_institutional_memory_gets_a_substantive_three_paragraph_general_answer():
    question = "What is institutional memory, and why does it matter?"
    answer = compose_recovery(question)
    paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]

    assert len(paragraphs) == 3
    assert paragraphs[0].casefold().startswith("institutional memory is the knowledge")
    assert "records why a policy was adopted" in paragraphs[1]
    assert "preserving the reasons" in paragraphs[2]
    assert not composition.is_generic_nonanswer(question, answer)
    assert not composition.is_meta_answer_failure(answer)
    assert "Living Archive's formal definition" not in answer


def test_shared_definition_recovery_generalizes_across_concepts():
    cases = {
        "What is collective memory, and why does it matter?": "shared understanding of a group's past",
        "What is organizational learning, and why does it matter?": "uses experience and evidence",
        "What is governance, and why does it matter?": "establishes purpose, makes decisions",
        "What is administration, and why does it matter?": "coordination and execution",
        "What is institutional responsibility, and why does it matter?": "obligation to answer for its decisions",
    }
    for question, required in cases.items():
        answer = compose_recovery(question)
        paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]
        assert len(paragraphs) == 3
        assert required in answer
        assert not composition.is_generic_nonanswer(question, answer)


def test_unknown_definition_is_honest_and_not_circular_meta_commentary():
    question = "What is quantum stewardship, and why does it matter?"
    answer = compose_recovery(question)
    paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]
    assert len(paragraphs) == 3
    assert "I can't define Quantum stewardship reliably" in answer
    assert "Living Archive" not in answer
    assert not composition.is_generic_nonanswer(question, answer)


def test_runtime_provider_exhaustion_boundary_uses_recovery_and_fails_closed():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_provider_exhaustion_response(")
    end = source.index("\n\ndef _basic_inquiry_round1_deterministic_response(", start)
    boundary = source[start:end]

    assert "_compose_provider_exhaustion_recovery(" in boundary
    assert "_guide_composition.is_generic_nonanswer(query, _shared_definition)" in boundary
    assert "rejected_non_substantive_recovery" in boundary
    assert '"doorway_title": title if recommendation_available else ""' in source
