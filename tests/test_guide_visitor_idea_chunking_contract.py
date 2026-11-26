"""Regression tests for visitor-friendly semantic idea chunking."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_general_guide_contract_requires_semantic_chunks_without_a_fixed_template():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    required = (
        "IDEA-CHUNKING AND READER BREATHING ROOM",
        "Each paragraph should carry one main conceptual move",
        "blank line between units",
        "roughly 1–3 sentences per paragraph",
        "Preserve nuance, reasoning, and necessary qualifications",
        "do not manufacture sections",
    )
    for phrase in required:
        assert phrase in source
    assert "Do not impose a fixed number of paragraphs or a universal sequence" in source
    assert "VISITOR IDEA-CHUNKING AND READABILITY:" in source
    assert "The visitor should be able to pause after each idea" in source


def test_guide_answer_css_gives_semantic_chunks_readable_spacing_and_mobile_rhythm():
    source = (
        ROOT / "wordpress/living-archive-answer-doorway-standard/assets/answer-doorway.css"
    ).read_text(encoding="utf-8")
    assert "#archive-response-text > p" in source
    assert "margin: 0 0 1.05em" in source
    assert "line-height: 1.72" in source
    assert "@media (max-width: 700px)" in source
    assert "margin-bottom: 1.15em" in source
    assert "#archive-response-text li" in source


def test_guide_answer_renderer_preserves_backend_semantic_boundaries_instead_of_splitting_sentences():
    source = (
        ROOT / "wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.329.js"
    ).read_text(encoding="utf-8")
    assert "marked.parse(responseForPresentation)" in source
    assert "responseForPresentation.split" not in source
    assert "responseText.replaceChildren" in source
