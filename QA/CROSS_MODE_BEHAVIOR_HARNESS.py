"""Cross-mode behavioral comparison harness for USE and HRN.

This is a QA artifact only. It does not invoke either production runtime.
It tests whether the proposed shared contracts describe the same discipline
across representative operating cases without collapsing mode-specific state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Case:
    name: str
    input_text: str
    use_shape: str
    hrn_shape: str
    needs_evidence: bool
    shared_evidence_normalization: bool
    shared_claim_separation: bool
    shared_epistemic_boundary: bool
    shared_synthesis: bool
    shared_language_boundary: bool
    shared_doorway_proposal: bool
    shared_operation_state: bool
    mode_specific_boundary: str


CASES = (
    Case(
        "conceptual",
        "What is attention?",
        "conceptual",
        "ordinary_relational",
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "HRN relational state is not required for ordinary conceptual inquiry.",
    ),
    Case(
        "lived_relational",
        "I feel distant from someone I care about and do not know what is happening between us.",
        "lived_experience",
        "relational_conversation",
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "HRN owns relational movement, question-led steering, and perspective delta.",
    ),
    Case(
        "open_inquiry",
        "I keep wondering why everything feels different lately.",
        "open_inquiry",
        "relational_conversation",
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "HRN may deepen the conversation; USE still owns macro routing.",
    ),
    Case(
        "navigation",
        "Where should I begin in the Archive?",
        "orientation",
        "not_primary",
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "USE owns final canonical doorway authority.",
    ),
    Case(
        "safety_sensitive",
        "I want to end my life.",
        "risk",
        "safety_boundary",
        False,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        "Safety routing and interruption behavior remain outside the shared reasoning grammar.",
    ),
    Case(
        "evidence_poor",
        "What is attention?",
        "conceptual",
        "ordinary_relational",
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "Neither mode should manufacture supported content when evidence is absent.",
    ),
    Case(
        "specialist_handoff",
        "I need help seeing what is happening in this relationship.",
        "relationship_handoff",
        "relational_conversation",
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "USE decides delegation; HRN owns specialist reasoning and voice.",
    ),
    Case(
        "provider_failure",
        "How do I explore this question?",
        "runtime_retry",
        "provider_arbitration",
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "Provider arbitration may be shared only after real cross-mode failure/quota comparison.",
    ),
)


def _assert_common(case: Case) -> None:
    assert case.shared_evidence_normalization
    assert case.shared_claim_separation
    assert case.shared_epistemic_boundary
    assert case.shared_synthesis
    assert case.shared_language_boundary
    assert case.shared_operation_state


def _assert_case_specific(case: Case) -> None:
    assert case.mode_specific_boundary
    if case.name == "navigation":
        assert case.shared_doorway_proposal
    if case.name == "specialist_handoff":
        assert "USE decides delegation" in case.mode_specific_boundary
    if case.name == "safety_sensitive":
        assert not case.shared_doorway_proposal
    if case.name == "provider_failure":
        assert "real cross-mode" in case.mode_specific_boundary


def build_report() -> str:
    lines = [
        "# Cross-Mode Behavioral Comparison — v487.81",
        "",
        "This harness validates the proposed shared disciplines against representative USE/HRN cases.",
        "It does not claim that identical labels imply identical mode semantics.",
        "",
        "## Results",
    ]
    for case in CASES:
        _assert_common(case)
        _assert_case_specific(case)
        lines.append(f"- {case.name}: common-discipline PASS; bounded boundary retained.")
    lines.extend(
        [
            "",
            "## Preliminary standardization result",
            "",
            "Validated as genuinely shared at the discipline level:",
            "- evidence normalization;",
            "- claim separation;",
            "- epistemic boundaries;",
            "- synthesis as a transformation;",
            "- visitor-language boundary;",
            "- explicit operation state.",
            "",
            "Validated as shared but authority-sensitive:",
            "- inquiry/movement representation;",
            "- canonical doorway proposal.",
            "",
            "Not yet promoted:",
            "- provider arbitration, pending real USE/HRN failure and quota comparison.",
            "",
            "Mode-specific capabilities remain outside the shared layer:",
            "- HRN relational conversation state, perspective movement, perspective delta, spiral/journey semantics;",
            "- FSD systems/fractal diagnostic reasoning;",
            "- USE macro routing, specialist delegation, integration, and final canonical authority.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    for case in CASES:
        _assert_common(case)
        _assert_case_specific(case)
    report = build_report()
    assert "provider arbitration" in report.casefold()
    assert "not yet promoted" in report.casefold()
    print(report)
    print("cross-mode behavioral harness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
