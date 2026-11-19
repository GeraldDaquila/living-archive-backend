"""Regression tests for evidence-backed personal-reference resolution."""
from personal_reference_resolution import (
    compose_teaching_conflict_protocol,
    is_personal_reference_question,
    is_teaching_conflict_reference,
    teaching_conflict_source_urls,
)

QUERY = (
    "What is my protocol when a teaching conflicts with my conscience, "
    "lived experience, or care for others?"
)

# Compact excerpts copied from the current published WordPress source bodies.
# These deliberately use real source language rather than synthetic marker lists.
SOURCE_TEXT = {
    "Analytical Procedure": (
        "Inquiry begins with careful attention. The first responsibility is to understand "
        "what is being encountered before attempting to explain it. Observation seeks "
        "description before judgment, pattern before theory, and reality before preference. "
        "Clarifying the question helps determine the appropriate forms of evidence, standards "
        "of reasoning, and level of claim required. Evidence is sought according to the nature "
        "of the question. Empirical investigation, historical records, lived experience, "
        "structural patterns, philosophical reflection, and cross-disciplinary insight may "
        "each contribute where appropriate. Every explanation has limits. Responsible inquiry "
        "asks where an explanation applies, where it becomes uncertain, what assumptions it "
        "depends upon, and what questions remain unresolved."
    ),
    "Discernment Foundations": (
        "Discernment is the disciplined practice of learning how to observe clearly, think "
        "critically, recognize patterns, question assumptions, regulate emotional reactivity, "
        "and remain grounded while navigating complexity. Separate Events From Interpretation. "
        "An event occurs. Then explanation, commentary, and reaction gather around it. "
        "Discernment begins by asking: What actually happened? What is verified? What remains "
        "speculative? Slow Down Before Concluding. Urgency often distorts perception. Discernment "
        "often requires slowing down, revisiting information later, examining multiple "
        "perspectives, and resisting the pressure to react immediately. Discernment therefore "
        "includes ethical responsibility: avoiding manipulation, resisting dehumanization, "
        "remaining open to revision, acknowledging uncertainty honestly."
    ),
    "Discernment, Authority, and Ethical Access": (
        "Discernment is not intuition alone. It is the capacity to pause, differentiate, and "
        "refrain. True discernment includes knowing when not to interpret, recognizing projection "
        "versus perception, allowing uncertainty to remain unresolved, and distinguishing "
        "curiosity from responsibility. Ethical authority is demonstrated through accountability "
        "for impact, willingness to be corrected, transparency about limits, and refusal to speak "
        "beyond jurisdiction. Ethical access requires consent of those affected, clarity of "
        "purpose, respect for boundaries, and acceptance that some material remains inaccessible. "
        "That insight grants permission to intervene is an explicitly rejected assumption."
    ),
    "My Approach": (
        "One of the guiding principles of my work is that different questions require different "
        "methods of inquiry. The empirical sciences have given humanity extraordinary tools for "
        "understanding the physical world. Psychology offers valuable frameworks for understanding "
        "behavior and development. Philosophy helps us examine assumptions and clarify ideas. "
        "While many contemplative claims cannot be verified through the same methods used in the "
        "natural sciences, they have remained part of humanity's search for meaning. I do not "
        "present contemplative work as scientific proof, nor do I dismiss it simply because it "
        "addresses questions that science was not designed to answer. The goal is never to replace "
        "a person's judgment. The goal is to deepen it."
    ),
    "Revision Protocol": (
        "No method remains trustworthy if it cannot be revised. Understanding grows through "
        "observation, criticism, reflection, and experience. As new evidence emerges, stronger "
        "explanations are developed, and previously unseen relationships become visible, "
        "responsible inquiry requires the willingness to reconsider earlier conclusions. "
        "Revision follows understanding. Revision preserves continuity. Revision remains "
        "transparent. Revision welcomes criticism. Criticism is evaluated according to the "
        "quality of its reasoning, evidence, explanatory power, and capacity to illuminate "
        "reality more clearly. Every conclusion remains provisional in principle."
    ),
}


def _documents():
    urls = teaching_conflict_source_urls()
    titles = (
        "Analytical Procedure",
        "Discernment Foundations",
        "Discernment, Authority, and Ethical Access",
        "My Approach",
        "Revision Protocol",
    )
    return [
        {"title": title, "url": url, "text": SOURCE_TEXT[title]}
        for title, url in zip(titles, urls)
    ]


def test_personal_reference_detector_selects_teaching_conflict_family():
    assert is_personal_reference_question(QUERY)
    assert is_teaching_conflict_reference(QUERY)
    assert not is_teaching_conflict_reference("What is a teaching protocol?")
    assert not is_teaching_conflict_reference("What is my protocol for organizing a project?")


def test_teaching_conflict_resolution_uses_published_source_content():
    result = compose_teaching_conflict_protocol(QUERY, _documents())
    assert result is not None
    assert len(result["documents"]) == 5
    assert result["doorway"]["title"] == "Analytical Procedure"
    assert "source-grounded discernment synthesis" in result["response"]
    assert "not a quotation" in result["response"]
    assert "conscience deserves serious attention" in result["response"].casefold()
    assert "not automatic proof" in result["response"].casefold()
    assert result["evidence_resolution"]["status"] == "complete"
    assert result["evidence_resolution"]["corpus_absence_proven"] is False


def test_missing_optional_supporting_source_does_not_destroy_valid_core_evidence():
    docs = _documents()[:3]
    result = compose_teaching_conflict_protocol(QUERY, docs)
    assert result is not None
    assert len(result["documents"]) == 3
    assert result["evidence_resolution"]["status"] == "partial"
    assert "My Approach" not in result["response"]
    assert "Revision Protocol" not in result["response"]


def test_missing_required_core_source_fails_closed_without_claiming_archive_absence():
    assert compose_teaching_conflict_protocol(QUERY, _documents()[1:]) is None


def test_source_urls_with_www_and_query_parameters_still_match_canonical_identity():
    docs = _documents()
    docs[0]["url"] = "https://www.geralddaquila.com/analytical-procedure/?utm_source=guide"
    result = compose_teaching_conflict_protocol(QUERY, docs)
    assert result is not None
    assert result["documents"][0]["title"] == "Analytical Procedure"


def test_wrong_canonical_source_body_is_rejected():
    docs = _documents()
    docs[0] = {
        "title": "Revision Protocol",
        "url": docs[0]["url"],
        "text": SOURCE_TEXT["Revision Protocol"],
    }
    assert compose_teaching_conflict_protocol(QUERY, docs) is None


def test_main_routes_verified_personal_references_before_provider_fallback():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    assert "is_teaching_conflict_reference(query)" in source
    assert "_wordpress_fetch_selected_canonical_body, _source_urls" in source
    assert "if personal_reference_result:" in source
    assert "provider_independent=True" in source
