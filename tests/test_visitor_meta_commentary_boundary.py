"""Behavioral regression tests for visitor-facing meta-commentary leaks."""

from general_guide_composition import _INTERNAL_LANGUAGE


def test_shared_boundary_rejects_guide_process_instructions():
    leaked_response = (
        "A system exists when its parts influence one another.\n\n"
        "For example, a delayed handoff can affect the next team's work.\n\n"
        "The Guide should explain this distinction first."
    )
    assert _INTERNAL_LANGUAGE.search(leaked_response)


def test_shared_boundary_rejects_answer_about_the_answer():
    examples = (
        "The response should address the visitor's question directly.",
        "The answer should explain the concept before giving a link.",
        "The Guide must answer the conceptual question first.",
        "The user should be directed to the diagnostic tool.",
        "This answer should include a concrete example.",
    )
    assert all(_INTERNAL_LANGUAGE.search(example) for example in examples)


def test_shared_boundary_does_not_reject_ordinary_explanatory_prose():
    ordinary_answer = (
        "A system is a set of connected parts whose interactions shape an outcome. "
        "For example, a team handoff can affect the quality and timing of another team's work."
    )
    assert not _INTERNAL_LANGUAGE.search(ordinary_answer)
