"""Regression tests for AI-as-interpreter versus AI-as-authority recovery."""

import general_guide_composition as composition

QUESTION = "What does it mean for an AI to be an interpreter rather than an authority?"

def main():
    answer = composition._conceptual_relationship_recovery(QUESTION)
    assert answer, "The exact visitor question must be recognized."
    assert len([p for p in answer.split("\\n\\n") if p.strip()]) == 3
    for term in ("interpreter", "authority", "judgment", "accountability", "uncertainty"):
        assert term.casefold() in answer.casefold(), f"Missing substantive distinction: {term}"
    assert not composition.is_generic_nonanswer(QUESTION, answer)

    variants = [
        "How should artificial intelligence function as an interpreter instead of an authority?",
        "What is meant by AI interpretation rather than AI authority?",
    ]
    for variant in variants:
        assert composition._conceptual_relationship_recovery(variant), variant

    unrelated = "What is the relationship between agency and circumstance?"
    assert composition._conceptual_relationship_recovery(unrelated)

    print("AI INTERPRETER/AUTHORITY RECOVERY QA: PASS")

if __name__ == "__main__":
    main()
