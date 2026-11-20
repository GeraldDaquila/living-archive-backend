from pathlib import Path

from guide_critique_evidence_integrity import (
    filter_critique_evidence,
    is_substantive_archive_evidence,
)
from guide_reflexive_critique import build_reflexive_critique_plan


def test_rejects_wordpress_header_image_metadata_as_evidence():
    fragment = {
        "title": "Life Understood",
        "url": "https://geralddaquila.com/",
        "text": (
            "Optimized WebP copy for the site header; original PNG retained unchanged. "
            'data-image-caption="" data-large-file="https://i0.wp.com/geralddaquila.com/'
            "wp-content/uploads/header.png"
        ),
    }
    assert not is_substantive_archive_evidence(fragment)


def test_retains_substantive_foundational_archive_passage():
    document = {
        "title": "The Living Archive: A Sensemaking Infrastructure",
        "url": "https://geralddaquila.com/living-archive/",
        "text": (
            "The Living Archive is a sensemaking infrastructure for navigating "
            "complexity, uncertainty, and human development. It distinguishes "
            "understanding from certainty and treats knowledge as revisable through "
            "evidence, reflection, and engagement with lived experience. Its claims "
            "about agency and interdependence should be examined through their "
            "definitions, scope, assumptions, and consequences in practice."
        ),
    }
    assert is_substantive_archive_evidence(document)


def test_filter_removes_media_context_and_marks_evidence_unavailable():
    context = {
        "generation_authority_protected_docs": [{
            "title": "Header image",
            "url": "https://geralddaquila.com/",
            "text": 'data-image-caption="" data-large-file="header.png" optimized WebP copy',
        }],
        "context_blocks": 'data-image-caption="" data-large-file="header.png"',
    }
    filtered = filter_critique_evidence(context)
    assert filtered["generation_authority_protected_docs"] == []
    assert filtered["context_blocks"] == ""
    assert filtered["evidence_sufficiency_unavailable"] is True
    assert filtered["_critique_evidence_integrity"]["removed_non_substantive_items"] == 2


def test_good_faith_critique_plan_is_answer_first_and_media_excluding():
    plan = build_reflexive_critique_plan(
        "What would constitute a good-faith critique of the Archive's worldview?"
    )
    assert plan is not None
    assert plan["version"] == "3.0"
    assert plan["response_contract"]["required_sequence"][0] == "define_good_faith_critique"
    assert "never replace the answer with a resource summary" in plan["retrieval_query"].lower() or (
        "does not supply or replace the methodological answer" in plan["retrieval_query"].lower()
    )
    assert "image captions" in plan["retrieval_query"].lower()
    assert "when_archive_sources_are_missing_answer_the_methodological_question_anyway" in plan["answer_requirements"]


def test_main_wires_evidence_gate_before_composition():
    source = Path("main.py").read_text(encoding="utf-8")
    fetch = source.index("context_data = use_core.fetch_canonical_context(resource_query)")
    gate = source.index("context_data = _filter_critique_evidence(context_data)", fetch)
    composition = source.index("composition_context = dict(context_data)", gate)
    assert fetch < gate < composition
