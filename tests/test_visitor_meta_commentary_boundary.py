"""Behavioral regression tests for visitor-facing meta-commentary leaks."""

from general_guide_composition import _INTERNAL_LANGUAGE, enforce_response_contracts


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



def test_final_response_contract_cannot_reintroduce_meta_commentary():
    question = "What makes a situation a system rather than a collection of separate problems?"
    response = enforce_response_contracts(question, "A system is a connected set of parts that influence one another.")
    paragraphs = [part.strip() for part in response.split("\\n\\n") if part.strip()]
    assert len(paragraphs) == 3
    assert "relationships must be evidenced rather than assumed" in response
    assert not _INTERNAL_LANGUAGE.search(response)
    assert "diagnostic tool" not in response.lower()


def test_final_boundary_preserves_ordinary_handoff_prose():
    question = "Explain why teams coordinate their work."
    candidate = (
        "Teams coordinate because each person's work affects what others can do. "
        "A clear handoff helps the next person continue without losing context.\\n\\n"
        "For example, a team can share status and constraints before work moves on.\\n\\n"
        "The Guide should explain this distinction first."
    )
    response = enforce_response_contracts(question, candidate)
    assert "clear handoff" in response
    assert "The Guide should explain" not in response
