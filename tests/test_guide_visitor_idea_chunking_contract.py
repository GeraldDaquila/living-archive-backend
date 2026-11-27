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
    assert "margin: 0 0 1.1em" in source
    assert "font-size: 18px !important" in source
    assert "line-height: 1.75 !important" in source
    assert "@media (max-width: 700px)" in source
    assert "margin-bottom: 1.2em !important" in source
    assert "line-height: 1.78 !important" in source
    assert "#archive-response-text li" in source
    plugin = (ROOT / "wordpress/living-archive-answer-doorway-standard/living-archive-answer-doorway-standard.php").read_text(encoding="utf-8")
    assert "Version: 1.0.5" in plugin
    assert "define('LA_ANSWER_DOORWAY_VERSION', '1.0.5')" in plugin


def test_guide_answer_renderer_preserves_backend_semantic_boundaries_instead_of_splitting_sentences():
    source = (
        ROOT / "wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.333.js"
    ).read_text(encoding="utf-8")
    assert "function renderGuideAnswerContent(" in source
    assert "marked.parse(text)" in source
    assert "target.replaceChildren" in source
    assert "text.split(/\\n{2,}/)" in source
    assert "text.split(/[^\\n.!?]+[.!?]/)" not in source


def test_substantive_single_block_is_rejected_but_chunked_answer_is_admitted():
    from general_guide_composition import _requires_visitor_idea_chunking

    sentences = [
        "Pain can be present without defining the whole person, because an experience is not the same thing as an identity.",
        "Naming the feeling creates a little distance, allowing someone to notice it without denying that it matters.",
        "The distinction also protects against the opposite mistake of suppressing pain or pretending it has disappeared.",
        "Other relationships, commitments, interests, and values remain part of a person's life while pain is present.",
        "A practical response can therefore acknowledge the feeling while keeping it in proportion to the wider self.",
        "This does not make the pain trivial; it makes room for the person to remain larger than the pain.",
    ]
    single_block = " ".join(sentences)
    chunked = "\n\n".join([" ".join(sentences[:2]), " ".join(sentences[2:4]), " ".join(sentences[4:])])

    assert len(single_block) >= 650
    assert _requires_visitor_idea_chunking(single_block)
    assert not _requires_visitor_idea_chunking(chunked)


def test_short_direct_answer_is_not_forced_into_multiple_paragraphs():
    from general_guide_composition import _requires_visitor_idea_chunking

    assert not _requires_visitor_idea_chunking(
        "Pain is an experience a person can acknowledge without treating it as their entire identity."
    )
