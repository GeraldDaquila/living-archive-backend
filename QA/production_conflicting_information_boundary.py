"""Production-baseline regression for conflicting-information discernment."""
import general_guide_composition as composition

QUERY = (
    "I feel overwhelmed by conflicting information and opinions. "
    "How can I regain my bearings and know what is real enough to act on?"
)

MALFORMED = (
    "A practical way to approach I feel overwhelmed by conflicting information and opinions. "
    "How can I regain my bearings and know what is real enough to act on is to begin by clarifying "
    "the outcome and the responsibilities involved.\n\n"
    "Next, compare a small number of realistic options against the purpose you are trying to serve. "
    "Consider likely benefits, foreseeable harms, and who carries the costs.\n\n"
    "Finally, act on the best-supported option and review the consequences."
)


def main():
    assert composition._requires_conflicting_information_discernment(QUERY)
    recovery = composition._conflicting_information_discernment_recovery()
    assert composition._has_conflicting_information_discernment(recovery)

    bad = {
        "response": MALFORMED,
        "recommendation": {"title": "irrelevant doorway"},
        "doorway_title": "Irrelevant doorway",
        "doorway_url": "https://example.invalid/",
    }
    repaired = composition.enforce_conflicting_information_boundary(QUERY, bad)
    assert repaired is not bad
    assert composition._has_conflicting_information_discernment(repaired["response"])
    assert repaired["processing"] == "final_visitor_boundary_conflicting_information_recovery"
    assert repaired["recommendation"] is None
    assert repaired["doorway_title"] == ""
    assert repaired["doorway_url"] == ""

    good = {"response": recovery}
    assert composition.enforce_conflicting_information_boundary(QUERY, good) is good
    assert not composition._requires_conflicting_information_discernment(
        "What are three ways to organize my desk?"
    )
    print("PASS: production-baseline conflicting-information discernment contract")


if __name__ == "__main__":
    main()
