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

SOURCE_TEXT = {
    "Analytical Procedure": (
        "Observe. Clarify the question. Gather appropriate evidence. Develop explanations. "
        "Locate the level of claim. Examine the boundaries. Reflect upon implications. "
        "Remain open to revision. " + "A disciplined inquiry process. " * 20
    ),
    "Discernment Foundations": (
        "Separate Events From Interpretation. Slow Down Before Concluding. "
        "Discernment and Ethical Responsibility. Remain open to revision. "
        + "Observe clearly and remain grounded. " * 20
    ),
    "Discernment, Authority, and Ethical Access": (
        "Discernment is the capacity to pause, differentiate, and refrain. "
        "Consent of those affected. Willingness to be corrected. "
        "Transparency about limits. " + "Ethical authority is accountable. " * 20
    ),
    "Revision Protocol": (
        "Revision follows understanding. Revision welcomes criticism. "
        "Better evidence can require reconsideration. " + "Revision preserves continuity. " * 20
    ),
}

def _documents():
    urls = teaching_conflict_source_urls()
    titles = (
        "Analytical Procedure",
        "Discernment Foundations",
        "Discernment, Authority, and Ethical Access",
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
    assert not is_teaching_conflict_reference(
        "What is my protocol for organizing a project?"
    )

def test_teaching_conflict_resolution_requires_all_verified_source_bodies():
    result = compose_teaching_conflict_protocol(QUERY, _documents())
    assert result is not None
    assert len(result["documents"]) == 4
    assert result["doorway"]["title"] == "Analytical Procedure"
    assert "faithful synthesis" in result["response"]
    assert "conscience matters as an ethical signal" in result["response"]
    assert "not automatic proof" in result["response"]
    for step in (
        "Pause before concluding",
        "Observe what is actually in conflict",
        "Clarify the claim",
        "Gather and compare appropriate evidence",
        "Examine boundaries and ethical consequences",
        "Consider what the teaching produces in practice",
        "Withhold assent when the evidence is insufficient",
        "Remain correctable",
    ):
        assert step in result["response"]

def test_teaching_conflict_resolution_fails_closed_when_a_source_is_missing():
    assert compose_teaching_conflict_protocol(QUERY, _documents()[:-1]) is None

def test_teaching_conflict_resolution_rejects_wrong_canonical_source_body():
    docs = _documents()
    docs[0] = {
        "title": "A Different Page",
        "url": docs[0]["url"],
        "text": SOURCE_TEXT["Analytical Procedure"],
    }
    assert compose_teaching_conflict_protocol(QUERY, docs) is None

def test_teaching_conflict_resolution_rejects_incomplete_source_markers():
    docs = _documents()
    docs[1] = dict(docs[1], text="A short incomplete page body " * 20)
    assert compose_teaching_conflict_protocol(QUERY, docs) is None

def test_main_routes_verified_personal_references_before_provider_fallback():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    assert "is_teaching_conflict_reference(query)" in source
    assert "_wordpress_fetch_selected_canonical_body, _source_urls" in source
    assert "if personal_reference_result:" in source
    assert 'provider_independent=True' in source
    assert "generic_personal_protocol_not_invented=True" in source
