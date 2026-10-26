"""Regression QA for the system-wide default Gold Standard composition gate."""

import general_guide_composition as composition


def main():
    query = "What are the risks of charisma without constitutional restraint?"

    weak_answer = (
        "The risks are best understood by what it means and how it operates in practice.\n\n"
        "A useful explanation distinguishes the idea from nearby concepts and makes its implications visible.\n\n"
        "The precise meaning can vary by field or institution, so this is a general explanation."
    )
    assert composition._requires_three_paragraph_default(query) is True
    assert composition.is_generic_nonanswer(query, weak_answer) is True

    substantive_answer = (
        "Charisma without constitutional restraint can concentrate power around a leader and weaken independent checks.\n\n"
        "When followers treat personal loyalty as more important than shared rules, dissent can be silenced and mistakes can go uncorrected.\n\n"
        "Charisma is not inherently harmful; transparent rules, accountability, and independent review help keep influence answerable to the institution's purpose."
    )
    assert composition.is_generic_nonanswer(query, substantive_answer) is False

    # The rejection must apply regardless of whether a question matches a
    # named special-case handler: it is part of the default composition contract.
    other_query = "Why can confidence become dangerous in a leader?"
    generic_answer = (
        "This is best understood by what it means and how it operates in practice.\n\n"
        "A useful explanation distinguishes the idea from nearby concepts.\n\n"
        "The precise meaning can vary by field or institution."
    )
    assert composition._requires_three_paragraph_default(other_query) is True
    assert composition.is_generic_nonanswer(other_query, generic_answer) is True

    # Keep the default composition prompt's quality contract structural and
    # provider-independent: causal calibration, applied mechanisms, safeguards,
    # and conceptual distinctions must be present for every substantive answer.
    import inspect
    source = inspect.getsource(composition)
    for contract_phrase in (
        "Calibrate causal claims",
        "trace the chain from the source of influence or capability",
        "explain what each safeguard does in practice",
        "Make examples diagnostic, not decorative",
        "Avoid conceptual conflation",
        "Use a causal spine across the three paragraphs",
        "Prefer operational specificity over abstract virtue lists",
        "Make the example do analytical work",
        "check paragraph function as well as paragraph count",
        "do not let a general relational explanation stand in for Archive-specific substance",
        "Make conceptual answers operational",
        "evidence-to-doorway relevance check",
        "Separate three things explicitly when needed",
        "Archive-scoped meaning answer is circular meta-definition, not a substantive definition",
        "Archive-scoped meaning answer must define the actual concept in its opening paragraph",
    ):
        assert contract_phrase in source, f"Missing default composition contract: {contract_phrase}"

    print("DEFAULT GOLD STANDARD SUBSTANTIVE COMPOSITION QA: PASS")


if __name__ == "__main__":
    main()
