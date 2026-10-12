"""Regression QA for HRN internal-observer language and malformed visitor prose."""
from provider_bank import _hrn_surface_language_violation, _normalize_operation_result


BAD_RESPONSES = (
    "You described the visitor distinguishes between wanting to win and wanting to be heard; the core protectee is the relationship's sense of mutual validity. That detail does not settle what the other person meant.",
    "you distinguishes between wanting to win and wanting to be heard. The conversation can end here without forcing a verdict.",
    "The conversation centered on understanding the experience of feeling unheard in friendship disagreement. The details described do not establish every part of what they mean.",
    "The visitor is protecting the friendship's capacity for mutual witnessing. Witness protection is the core of the relationship's mutual validity.",
    "New: the counter is a distinct relational move, not just a failure to listen. That is part of what was described, not proof of every possible meaning. A change can be noticed without treating an explanation for it as established fact. The other person's intention remains unconfirmed by the information here.",
)

GROUNDED_RESPONSE = (
    "You said you feel unheard when you and your friend disagree. You want to understand what happens between you in those moments without assuming what your friend intends. The difference between disagreeing about a topic and feeling unheard during the conversation is worth looking at separately."
)


def main():
    for response in BAD_RESPONSES:
        violation = _hrn_surface_language_violation(response)
        assert violation, f"Internal-observer or malformed prose passed: {response!r}"
        try:
            _normalize_operation_result(
                "hrn_relational",
                {
                    "response": response,
                    "question": "Where does that happen most clearly?",
                    "rest": False,
                    "use_resource": False,
                    "resource_intro": "",
                },
            )
        except ValueError as exc:
            assert "visitor-surface contract violation" in str(exc)
        else:
            raise AssertionError("Invalid HRN prose must be rejected before WordPress.")

    assert _hrn_surface_language_violation(GROUNDED_RESPONSE) == "", (
        "Concrete, qualified, visitor-grounded prose must remain eligible."
    )
    print("V489.103 HRN INTERNAL-OBSERVER LANGUAGE QA: PASS")


if __name__ == "__main__":
    main()
