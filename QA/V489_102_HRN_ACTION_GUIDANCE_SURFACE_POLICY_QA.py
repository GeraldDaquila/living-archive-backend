"""Regression QA for rejecting abstract causal and coaching-like HRN prose."""
from provider_bank import _hrn_surface_language_violation, _normalize_operation_result


COACHING_RESPONSE = (
    "When a disagreement leaves you feeling unheard, the friction is rarely just "
    "about the topic being debated. It often reveals a gap between reaching an "
    "agreement and simply acknowledging what the other person actually experienced. "
    "Noticing whether the struggle is about winning a point or making room for two "
    "distinct viewpoints allows you to see where the conversation stops being a "
    "shared dialogue."
)

GROUNDED_RESPONSE = (
    "You said you feel unheard when you and your friend disagree. You want to "
    "understand what happens between you in those moments without assuming what "
    "your friend intends. The difference between disagreeing about a topic and "
    "feeling unheard during the conversation is worth looking at separately."
)


def _parsed(response, question):
    return {
        "response": response,
        "question": question,
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }


def main():
    violation = _hrn_surface_language_violation(COACHING_RESPONSE)
    assert violation, "Known abstract/coaching-like HRN prose passed the Provider Bank policy."
    try:
        _normalize_operation_result(
            "hrn_relational",
            _parsed(COACHING_RESPONSE, "What happens just before you begin to feel unheard?"),
        )
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("Abstract/coaching-like HRN prose must be rejected before WordPress.")

    assert _hrn_surface_language_violation(
        "Noticing the difference allows you to see what happens next."
    ), "Action-guidance phrasing must be rejected."
    assert _hrn_surface_language_violation(
        "The friction is rarely just about the topic being debated."
    ), "Abstract causal framing must be rejected."

    assert _hrn_surface_language_violation(GROUNDED_RESPONSE) == "", (
        "Concrete, qualified, visitor-grounded prose must remain eligible."
    )
    print("V489.102 HRN ACTION-GUIDANCE SURFACE-POLICY QA: PASS")


if __name__ == "__main__":
    main()
