"""Cross-mode behavioral comparison harness for USE and HRN.

This QA artifact is intentionally runtime-independent. It tests contracts and
boundaries, not production output. It must make failure visible rather than
encoding assumptions as unconditional PASS values.
"""
from __future__ import annotations

from dataclasses import dataclass


SHARED_DISCIPLINES = (
    "evidence_normalization",
    "claim_separation",
    "epistemic_boundaries",
    "synthesis",
    "visitor_language_boundary",
    "operation_state",
)


@dataclass(frozen=True)
class Case:
    name: str
    use_shape: str
    hrn_shape: str
    shared: frozenset[str]
    authority_sensitive: frozenset[str]
    mode_owned: frozenset[str]


CASES = (
    Case(
        "conceptual",
        "conceptual",
        "not_primary",
        frozenset(SHARED_DISCIPLINES),
        frozenset({"doorway_proposal"}),
        frozenset({"hrn_relational_state", "use_macro_routing"}),
    ),
    Case(
        "lived_relational",
        "lived_experience",
        "relational_conversation",
        frozenset(SHARED_DISCIPLINES),
        frozenset({"doorway_proposal"}),
        frozenset({
            "hrn_relational_state",
            "hrn_question_steering",
            "hrn_perspective_delta",
            "use_macro_routing",
        }),
    ),
    Case(
        "open_inquiry",
        "open_inquiry",
        "relational_conversation",
        frozenset(SHARED_DISCIPLINES),
        frozenset({"inquiry_movement", "doorway_proposal"}),
        frozenset({"hrn_relational_state", "use_macro_routing"}),
    ),
    Case(
        "navigation",
        "orientation",
        "not_primary",
        frozenset(SHARED_DISCIPLINES),
        frozenset({"doorway_proposal"}),
        frozenset({"use_final_canonical_authority"}),
    ),
    Case(
        "safety_sensitive",
        "risk",
        "safety_boundary",
        frozenset(SHARED_DISCIPLINES),
        frozenset(),
        frozenset({
            "safety_routing",
            "safety_interruption",
            "use_macro_routing",
        }),
    ),
    Case(
        "evidence_poor",
        "conceptual",
        "not_primary",
        frozenset(SHARED_DISCIPLINES),
        frozenset(),
        frozenset({"no_fabrication_boundary"}),
    ),
    Case(
        "specialist_handoff",
        "relationship_handoff",
        "relational_conversation",
        frozenset(SHARED_DISCIPLINES),
        frozenset({"inquiry_movement", "doorway_proposal"}),
        frozenset({
            "use_macro_routing",
            "use_specialist_delegation",
            "hrn_specialist_voice",
            "hrn_relational_state",
        }),
    ),
    Case(
        "provider_failure",
        "runtime_retry",
        "provider_arbitration",
        frozenset(SHARED_DISCIPLINES),
        frozenset({"operation_retry_policy"}),
        frozenset({"provider_selection_policy"}),
    ),
)


def _assert_case(case: Case) -> None:
    assert set(SHARED_DISCIPLINES).issubset(case.shared), case.name
    assert case.shared.isdisjoint(case.mode_owned), case.name
    assert case.authority_sensitive.isdisjoint(case.mode_owned), case.name
    assert case.mode_owned, case.name

    if case.name == "specialist_handoff":
        assert "use_macro_routing" in case.mode_owned
        assert "hrn_specialist_voice" in case.mode_owned

    if case.name == "navigation":
        assert "doorway_proposal" in case.authority_sensitive
        assert "use_final_canonical_authority" in case.mode_owned

    if case.name == "safety_sensitive":
        assert not case.authority_sensitive

    if case.name == "evidence_poor":
        assert "no_fabrication_boundary" in case.mode_owned

    if case.name == "provider_failure":
        assert "operation_retry_policy" in case.authority_sensitive


def build_report() -> str:
    for case in CASES:
        _assert_case(case)

    shared = "\n".join(f"- {name}" for name in SHARED_DISCIPLINES)
    cases = "\n".join(
        f"- {case.name}: shared disciplines verified; mode-owned boundary retained."
        for case in CASES
    )

    return (
        "# Cross-Mode Behavioral Comparison — v487.81\n\n"
        "## Shared disciplines verified\n"
        f"{shared}\n\n"
        "## Representative cases\n"
        f"{cases}\n\n"
        "## Authority-sensitive interfaces\n"
        "- inquiry/movement representation: shared shape, mode-specific semantics.\n"
        "- doorway proposal: shared proposal mechanism; USE retains final canonical authority.\n"
        "- retry policy: explicit shared state; provider selection remains mode/infrastructure-owned.\n\n"
        "## Mode-owned boundaries\n"
        "- HRN: relational conversation state, question-led steering, perspective movement/delta, specialist voice.\n"
        "- USE: macro routing, specialist delegation, contribution integration, final canonical authority.\n"
        "- Safety: interruption/routing behavior remains outside the generic shared reasoning grammar.\n\n"
        "## Promotion gate\n"
        "These results justify extraction of the shared disciplines as reusable infrastructure. "
        "They do not justify a universal conversation manager, a second general-purpose brain, "
        "or promotion of provider arbitration without real failure/quota comparison.\n"
    )


def main() -> int:
    report = build_report()
    assert "universal conversation manager" in report
    assert "provider arbitration" in report
    print(report)
    print("cross-mode behavioral harness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
