"""Behavioral regression tests for visitor-facing meta-commentary leaks."""

from general_guide_composition import _INTERNAL_LANGUAGE, enforce_response_contracts


def test_shared_sanitizer_removes_retrieval_metadata_source_labels_and_emoji():
    from general_guide_composition import _sanitize_candidate

    leaked = (
        '"Why Modern Systems Become Vulnerable Under Pressure" Meta Description: '
        'Explore how complexity contributes to fragility. '
        '"Complexity and Institutional Fragility" '
        'Institutional Cornerstones (⭐ Institutional Cornerstones)'
    )
    cleaned = _sanitize_candidate(leaked)
    assert "Meta Description" not in cleaned
    assert "⭐" not in cleaned
    assert "✨" not in cleaned
    assert "Complexity and Institutional Fragility" not in cleaned
    assert "Institutional Cornerstones" not in cleaned


def test_default_composition_instructions_forbid_raw_retrieval_material():
    from general_guide_composition import _GENERAL_GUIDE_SYSTEM

    assert "RETRIEVAL-TO-RESPONSE COMPOSITION BOUNDARY" in _GENERAL_GUIDE_SYSTEM
    assert 'including "Meta Description"' in _GENERAL_GUIDE_SYSTEM
    assert "Never emit emoji or decorative glyphs" in _GENERAL_GUIDE_SYSTEM
    assert "first paragraph directly answers the visitor's actual question" in _GENERAL_GUIDE_SYSTEM


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
    paragraphs = [part.strip() for part in response.split("\n\n") if part.strip()]
    assert len(paragraphs) == 3
    assert "relationships must be evidenced rather than assumed" in response
    assert not _INTERNAL_LANGUAGE.search(response)
    assert "diagnostic tool" not in response.lower()


def test_final_boundary_preserves_ordinary_handoff_prose():
    question = "Explain why teams coordinate their work."
    candidate = (
        "Teams coordinate because each person's work affects what others can do. "
        "A clear handoff helps the next person continue without losing context.\n\n"
        "For example, a team can share status and constraints before work moves on.\n\n"
        "The Guide should explain this distinction first."
    )
    response = enforce_response_contracts(question, candidate)
    assert "clear handoff" in response
    assert "The Guide should explain" not in response



def test_catalogue_style_retrieval_blocks_are_not_accepted_as_answers():
    from general_guide_composition import _sanitize_candidate

    leaked = (
        '"Fragility does not always emerge through dramatic collapse; more often, it appears through subtle erosion: declining trust, institutional paralysis, systemic inefficiency, and widening gaps between governance structures and lived reality." (Complexity and Institutional Fragility)\\n\\n'
        '"Exploring the Stewardship of Organizations, Leadership, and Institutional Life Discover essays on power, governance, stewardship, organizational design, and the constitutional foundations of healthy institutions." (Institutional Cornerstones) "Document Type: Canonical Landing Page Status: Foundational Institutional Collection Purpose: To introduce the principal essays exploring stewardship at the institutional scale through organizations, governance, leadership, and systems of collective responsibility." (Institutional Cornerstones)\\n\\n'
        '"Translating Constitutional Architecture into Organizational Life Discover how stewardship becomes institutional practice across organizations and communities." (Institutional Stewardship) "Document Type: Canonical Reference Hub Status: Foundational Institutional Infrastructure Collection Authority: Institutional translation of the Constitutional Architecture."'
    )
    cleaned = _sanitize_candidate(leaked)
    assert "Document Type" not in cleaned
    assert "Collection Purpose" not in cleaned
    assert "Institutional Cornerstones" not in cleaned
    assert "Institutional Stewardship" not in cleaned
    assert "Fragility does not always emerge" not in cleaned
    assert "Exploring the Stewardship of Organizations" not in cleaned


def test_catalogue_only_candidate_is_rejected_instead_of_becoming_answer():
    from general_guide_composition import _sanitize_candidate

    catalogue_only = (
        '"Exploring the Stewardship of Organizations, Leadership, and Institutional Life." '
        'Document Type: Canonical Landing Page Status: Foundational Institutional Collection Purpose: '
        'To introduce the principal essays exploring stewardship at the institutional scale.'
    )
    assert _sanitize_candidate(catalogue_only) == ""



def test_definition_and_significance_question_rejects_neighboring_problem_solving_frame():
    from general_guide_composition import is_generic_nonanswer

    question = "What is institutional memory, and why does it matter?"
    off_task = (
        "The most useful explanation for why institutional memory, and why does it matter begins by distinguishing "
        "the immediate event from the conditions that made it more likely. A visible incident may be the trigger without being the whole cause.\n\n"
        "Look at the evidence, incentives, constraints, relationships, and decisions involved, and compare more than one plausible explanation.\n\n"
        "These are possibilities to test, not conclusions about a specific case. The strongest explanation accounts for the available facts."
    )
    assert is_generic_nonanswer(question, off_task)


def test_definition_and_significance_question_accepts_direct_three_paragraph_answer():
    from general_guide_composition import is_generic_nonanswer

    question = "What is institutional memory, and why does it matter?"
    answer = (
        "Institutional memory is the knowledge an organization retains from its decisions, experience, practices, and lessons over time.\n\n"
        "For example, recording why a policy was adopted helps new leaders understand the problem it was meant to solve instead of repeating an earlier mistake.\n\n"
        "Institutional memory matters when it preserves context as well as records; outdated assumptions must still be questioned as circumstances change."
    )
    assert not is_generic_nonanswer(question, answer)
