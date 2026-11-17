import pytest

from general_guide_composition import (
    _archive_passage_sources,
    _archive_passage_contrast_recovery,
    _has_archive_passage_contrast_structure,
    _requires_archive_passage_contrast,
    archive_passage_contrast_recovery_from_context,
)

QUESTION = (
    "Find two relevant Archive passages that disagree in emphasis. "
    "How should the Guide represent each passage before attempting any synthesis?"
)

SOURCES = [
    {"title": "Passage Alpha", "url": "https://geralddaquila.com/alpha/", "text": "A" * 120},
    {"title": "Passage Beta", "url": "https://geralddaquila.com/beta/", "text": "B" * 120},
]


def test_explicit_two_passage_contrast_request_is_recognized():
    assert _requires_archive_passage_contrast(QUESTION)
    assert not _requires_archive_passage_contrast("What is a passage in the Living Archive?")


def test_only_two_distinct_canonical_passages_with_text_are_eligible():
    docs = SOURCES + [dict(SOURCES[0])]
    assert [item["title"] for item in _archive_passage_sources(docs)] == ["Passage Alpha", "Passage Beta"]
    assert len(_archive_passage_sources([SOURCES[0], dict(SOURCES[0])])) == 1


def test_answer_must_represent_both_passages_before_synthesis():
    response = (
        "Passage 1 — Passage Alpha: its emphasis is represented in its own terms.\n\n"
        "Passage 2 — Passage Beta: its distinct emphasis is represented in its own terms.\n\n"
        "Only after representing both passages should the Guide identify the tension "
        "and offer a cautious synthesis."
    )
    assert _has_archive_passage_contrast_structure(QUESTION, response, SOURCES)


def test_generic_refusal_or_synthesis_without_two_representations_fails():
    generic = "The Archive contains many perspectives. It is important to respect them before synthesizing."
    assert not _has_archive_passage_contrast_structure(QUESTION, generic, SOURCES)
    assert not _has_archive_passage_contrast_structure(QUESTION, "No reliable answer is available.", SOURCES)


def test_missing_second_source_cannot_be_misrepresented_as_a_comparison():
    assert not _has_archive_passage_contrast_structure(QUESTION, "Passage 1 — Passage Alpha", SOURCES[:1])


def test_terminal_provider_exhaustion_recovers_from_protected_context_documents():
    class Core:
        @staticmethod
        def context_blocks_to_documents(_blocks):
            return []

    recovered = archive_passage_contrast_recovery_from_context(
        QUESTION,
        Core(),
        {"generation_authority_protected_docs": SOURCES},
    )
    assert recovered is not None
    assert "Passage Alpha" in recovered["response"]
    assert "Passage Beta" in recovered["response"]
    assert recovered["processing"] == "archive_passage_contrast_terminal_recovery"


def test_terminal_provider_exhaustion_uses_context_block_documents_when_no_protected_docs():
    class Core:
        @staticmethod
        def context_blocks_to_documents(_blocks):
            return SOURCES

    recovered = archive_passage_contrast_recovery_from_context(
        QUESTION, Core(), {"context_blocks": "retrieved archive context"}
    )
    assert recovered is not None
    assert "Passage Alpha" in recovered["response"]
    assert "Passage Beta" in recovered["response"]


def test_terminal_provider_exhaustion_unions_partial_protected_docs_with_context_blocks():
    class Core:
        @staticmethod
        def context_blocks_to_documents(_blocks):
            return SOURCES[1:]

    recovered = archive_passage_contrast_recovery_from_context(
        QUESTION,
        Core(),
        {
            "generation_authority_protected_docs": SOURCES[:1],
            "context_blocks": "second retrieved archive passage",
        },
    )
    assert recovered is not None
    assert "Passage Alpha" in recovered["response"]
    assert "Passage Beta" in recovered["response"]


def test_terminal_provider_exhaustion_states_evidence_limit_instead_of_generic_failure():
    class Core:
        @staticmethod
        def context_blocks_to_documents(_blocks):
            return SOURCES[:1]

    recovered = archive_passage_contrast_recovery_from_context(
        QUESTION, Core(), {"context_blocks": "one retrieved archive passage"}
    )
    assert recovered is not None
    assert "could not verify two distinct" in recovered["response"]
    assert "I couldn't produce a reliable answer" not in recovered["response"]


def test_provider_exhaustion_recovery_preserves_both_sources_without_premature_synthesis():
    recovered = _archive_passage_contrast_recovery(QUESTION, SOURCES)
    assert recovered is not None
    assert "[Passage Alpha](https://geralddaquila.com/alpha/)" in recovered["response"]
    assert "[Passage Beta](https://geralddaquila.com/beta/)" in recovered["response"]
    assert "not yet a synthesis" in recovered["response"]


def test_provider_exhaustion_without_two_sources_states_specific_limit():
    recovered = _archive_passage_contrast_recovery(QUESTION, SOURCES[:1])
    assert recovered is not None
    assert "could not verify two distinct" in recovered["response"]
    assert "Libraries" in recovered["response"]
    assert "Passage Alpha" not in recovered["response"]
