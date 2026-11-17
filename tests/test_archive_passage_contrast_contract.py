import pytest

from general_guide_composition import (
    _archive_passage_sources,
    _archive_passage_contrast_recovery,
    _has_archive_passage_contrast_structure,
    _requires_archive_passage_contrast,
    archive_passage_contrast_recovery_from_context,
    is_preserved_archive_passage_contrast_recovery,
)

QUESTION = (
    "Find two relevant Archive passages that disagree in emphasis. "
    "How should the Guide represent each passage before attempting any synthesis?"
)

TOPIC_QUESTION = QUESTION.replace("relevant Archive passages", "Archive passages about stewardship")

SOURCES = [
    {"title": "Passage Alpha", "url": "https://geralddaquila.com/alpha/", "text": "A" * 120},
    {"title": "Passage Beta", "url": "https://geralddaquila.com/beta/", "text": "B" * 120},
]


def test_explicit_two_passage_contrast_request_is_recognized():
    assert _requires_archive_passage_contrast(QUESTION)
    assert not _requires_archive_passage_contrast("What is a passage in the Living Archive?")
    assert __import__("general_guide_composition")._archive_passage_contrast_topic_missing(QUESTION)
    module = __import__("general_guide_composition")
    assert not module._archive_passage_contrast_topic_missing(TOPIC_QUESTION)
    assert module._archive_passage_contrast_subject(TOPIC_QUESTION) == "stewardship"


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
        TOPIC_QUESTION,
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
        TOPIC_QUESTION, Core(), {"context_blocks": "retrieved archive context"}
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
        TOPIC_QUESTION,
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
        TOPIC_QUESTION, Core(), {"context_blocks": "one retrieved archive passage"}
    )
    assert recovered is not None
    assert "could not verify two distinct" in recovered["response"]
    assert "I couldn't produce a reliable answer" not in recovered["response"]


def test_final_boundary_preserves_already_validated_deterministic_recovery_without_context():
    topic_question = TOPIC_QUESTION
    recovered = _archive_passage_contrast_recovery(topic_question, SOURCES)
    assert recovered is not None
    assert is_preserved_archive_passage_contrast_recovery(recovered)


def test_final_boundary_does_not_trust_provider_generated_passage_markup():
    recovered = _archive_passage_contrast_recovery(TOPIC_QUESTION, SOURCES)
    recovered["provider"] = "external_provider"
    assert not is_preserved_archive_passage_contrast_recovery(recovered)


def test_final_boundary_rejects_duplicate_passage_urls_even_with_two_labels():
    recovered = _archive_passage_contrast_recovery(TOPIC_QUESTION, SOURCES)
    recovered["response"] = recovered["response"].replace(
        "https://geralddaquila.com/beta/",
        "https://geralddaquila.com/alpha/",
    )
    assert not is_preserved_archive_passage_contrast_recovery(recovered)


def test_provider_exhaustion_recovery_preserves_both_sources_without_premature_synthesis():
    recovered = _archive_passage_contrast_recovery(TOPIC_QUESTION, SOURCES)
    assert recovered is not None
    assert "[Passage Alpha](https://geralddaquila.com/alpha/)" in recovered["response"]
    assert "[Passage Beta](https://geralddaquila.com/beta/)" in recovered["response"]
    assert "not yet a synthesis" in recovered["response"]


def test_provider_exhaustion_without_two_sources_states_specific_limit():
    topic_question = TOPIC_QUESTION
    recovered = _archive_passage_contrast_recovery(topic_question, SOURCES[:1])
    assert recovered is not None
    assert "could not verify two distinct" in recovered["response"]
    assert "on that subject" in recovered["response"]
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
    assert 'elif safe.get("model") == "deterministic-topic-clarification":' in boundary
    assert '_gold_star_default_doorway()' in boundary
    assert "is_preserved_archive_passage_contrast_recovery" in boundary
    assert '_gold_star_default_doorway()' in boundary
    assert 'default_doorway = _normalize_authoritative_recommendation(' in boundary
    assert 'safe["doorway_rationale"] = default_doorway.get("rationale") if default_doorway else None' in boundary
    assert '_guide_restore_verified_doorway(safe, query)' not in boundary
    assert 'deterministic-topic-clarification' in boundary
    assert 'final_visitor_boundary_archive_passage_contrast_preserved' in boundary
    assert boundary.index("is_preserved_archive_passage_contrast_recovery") < boundary.index(
        "archive_passage_contrast_recovery_from_context"
    )
    assert boundary.index("archive_passage_contrast_recovery_from_context") < boundary.index(
        "is_comparative_traditions_question"
    )



def test_missing_subject_answers_method_first_then_requests_one_subject_and_selects_doorway():
    recovered = _archive_passage_contrast_recovery(QUESTION, [])
    assert recovered is not None
    assert recovered["model"] == "deterministic-topic-clarification"
    assert recovered["response"].startswith("Represent the two passages separately and symmetrically")
    assert "preserve its scope, qualifications, and intended audience" in recovered["response"]
    assert "Synthesis comes last" in recovered["response"]
    assert recovered["response"].rstrip().endswith(
        "Which subject or question should I search for in the Archive?"
    )
    assert recovered["doorway_title"] == "Sovereign Sensemaking Compass"
    assert recovered["doorway_url"] == "https://geralddaquila.com/the-sovereign-sensemaking-compass/"
    assert is_preserved_archive_passage_contrast_recovery(recovered)


def test_topicful_passage_contrast_request_is_not_misclassified_as_missing_subject():
    assert not __import__("general_guide_composition")._archive_passage_contrast_topic_missing(TOPIC_QUESTION)



def test_main_has_dedicated_canonical_body_retrieval_for_topicful_contrast_requests():
    from pathlib import Path
    import ast

    main_source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    ast.parse(main_source)
    source = main_source
    assert "_wordpress_search_canonical_candidates(" in source
    assert "_archive_passage_contrast_topic_missing(query)" in source
    assert "_archive_passage_sources(" in source
    assert "validated_distinct_passages=" in source
    assert "generation_authority_protected_docs" in source


def test_live_style_method_question_with_first_person_is_missing_subject():
    """Natural first-person wording must not be mistaken for a subject."""
    question = (
        "How should I represent two passages in the Archive that disagree "
        "in emphasis before synthesis?"
    )
    module = __import__("general_guide_composition")
    assert _requires_archive_passage_contrast(question)
    assert module._archive_passage_contrast_topic_missing(question)
    recovered = _archive_passage_contrast_recovery(question, [])
    assert recovered is not None
    assert recovered["model"] == "deterministic-topic-clarification"
    assert recovered["response"].startswith(
        "Represent the two passages separately and symmetrically"
    )
    assert recovered["doorway_title"] == "Sovereign Sensemaking Compass"
    assert recovered["doorway_rationale"]


def test_plain_show_me_two_passages_request_is_also_recognized():
    question = "Show me two passages in the Archive that disagree in emphasis."
    module = __import__("general_guide_composition")
    assert _requires_archive_passage_contrast(question)
    assert module._archive_passage_contrast_topic_missing(question)
    recovered = _archive_passage_contrast_recovery(question, [])
    assert recovered is not None
    assert recovered["model"] == "deterministic-topic-clarification"


def test_final_doorway_fallback_requires_frontend_renderable_rationale():
    """A URL/title without rationale is rejected by the shared browser doorway helper."""
    from pathlib import Path
    import ast

    main_source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    ast.parse(main_source)
    start = main_source.index("def _guide_restore_verified_doorway")
    end = main_source.index("def _guide_finalize_visitor_payload", start)
    function_source = main_source[start:end]
    assert "not str(doorway.get(\"rationale\") or \"\").strip()" in function_source
    assert "_gold_star_default_doorway()" in function_source



def test_topicless_clarification_uses_compass_not_a_guessed_conceptual_family():
    """Without a subject, the doorway must remain the approved broad continuation."""
    from pathlib import Path
    main_source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    start = main_source.index('if payload.get("model") == "deterministic-topic-clarification":')
    end = main_source.index('        else:', start)
    branch = main_source[start:end]
    assert "_gold_star_default_doorway()" in branch
    assert "_select_verified_doorway_conceptual_family(query)" not in branch
    assert 'safe["doorway_title"] = default_doorway.get("title")' in branch
    assert 'safe["doorway_rationale"] = default_doorway.get("rationale")' in branch
