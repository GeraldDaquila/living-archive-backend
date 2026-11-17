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


def test_final_visitor_boundary_enforces_passage_contrast_after_route_dispatch():
    """Guard against provider/legacy routes bypassing the source-bound recovery."""
    import ast
    from pathlib import Path

    main_source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(main_source)
    boundary_functions = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = ast.get_source_segment(main_source, node) or ""
        if 'response_text = str(payload.get("response") or "")' in body:
            boundary_functions.append(body)

    assert len(boundary_functions) == 1
    boundary = boundary_functions[0]
    assert "archive_passage_contrast_recovery_from_context" in boundary
    assert 'final_visitor_boundary_archive_passage_contrast' in boundary
    assert boundary.index("archive_passage_contrast_recovery_from_context") < boundary.index(
        "is_comparative_traditions_question"
    )


def test_response_selected_pair_is_validated_not_first_two_search_hits():
    docs = [
        {**SOURCES[0], "title": "Search Hit One"},
        {**SOURCES[1], "title": "Search Hit Two"},
        {"title": "Selected Passage Three", "url": "https://geralddaquila.com/three/", "text": "C" * 120},
        {"title": "Selected Passage Four", "url": "https://geralddaquila.com/four/", "text": "D" * 120},
    ]
    response = "Passage 1 — Selected Passage Three\nPassage 2 — Selected Passage Four"
    selected = _archive_passage_sources(docs, response)
    assert [item["title"] for item in selected] == ["Selected Passage Three", "Selected Passage Four"]


def test_context_extraction_preserves_full_candidate_pool_for_contrast():
    import ast
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "general_guide_composition.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_documents_from_context")
    body = ast.get_source_segment(source, function)
    assert "_archive_passage_contrast_candidate_pool" in body
    assert "12 if contrast_pool else 4" in body
    assert "documents.extend(item for item in parsed" in body


def test_main_has_dedicated_bounded_archive_contrast_discovery_axes():
    import ast
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_query_pipeline")
    body = ast.get_source_segment(source, function)
    assert "_requires_archive_passage_contrast(query)" in body
    assert '"stewardship control"' in body
    assert '"individual agency institutional systems"' in body
    assert '"growth structural limits"' in body
    assert '"human development governance"' in body
    assert "generation_authority_protected_docs" in body
