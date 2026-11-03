"""FSD Two-Quantum request contract.

This module is deliberately deterministic and side-effect free. It validates
raw answer selections and derives the two locked quantum summaries. It does
not call a model, retrieve evidence, persist answers, or generate a diagnosis.
"""
from __future__ import annotations

from typing import Any, Mapping

CONTRACT_VERSION = "fsd-two-quantum-v1"
QUESTION_COUNT = 10
OPTION_MIN = 0
OPTION_MAX = 3

SCALES = frozenset({
    "self",
    "relationships",
    "organization",
    "state",
    "civilization",
})

# Question indices are zero-based and follow the published FSD questionnaire.
# Q001 Correspondence: items 1-2 test whether emerging problems and difficult
# information can be surfaced; items 6-7 test whether consequences and learning
# reach the people/places able to perceive the system's actual condition.
# Q002 Correctability: items 3-5 test authority, capacity to change, and the
# incentives shaping action; items 8-10 test adaptation, recurrence, and leverage.
QUESTION_QUANTUM_RATIONALE = {
    0: "Problem recognition: whether a significant failure becomes visible.",
    1: "Difficult information: whether uncomfortable evidence can travel.",
    2: "Authority alignment: whether responsibility is matched by authority.",
    3: "Change capacity: whether attempts to alter patterns can take hold.",
    4: "Reinforcement: whether incentives sustain or reproduce the difficulty.",
    5: "Consequence proximity: whether decision-makers encounter decision effects.",
    6: "Learning: whether experience changes shared understanding and practice.",
    7: "Adaptation: whether changing conditions can prompt structural adjustment.",
    8: "Recurrence: whether responses alter underlying conditions or only symptoms.",
    9: "Leverage: whether meaningful points of correction can be located.",
}

QUANTUM_QUESTION_MAP = {
    "Q001_CORRESPONDENCE": (0, 1, 5, 6),
    "Q002_CORRECTABILITY": (2, 3, 4, 7, 8, 9),
}

PUBLIC_QUANTUM_LABELS = {
    "Q001_CORRESPONDENCE": "Correspondence",
    "Q002_CORRECTABILITY": "Correctability",
}


class FSDContractError(ValueError):
    """Raised when an FSD request violates the bounded input contract."""


def validate_diagnostic_payload(payload: Any) -> dict[str, Any]:
    """Validate raw answer indices and derive server-owned quantum summaries.

    The browser submits only ten option indices (0..3). It cannot submit
    authoritative scores, interpretations, evidence, URLs, or model/provider
    selections. Scale is optional until the visitor interface collects it.
    """
    if not isinstance(payload, Mapping):
        raise FSDContractError("Request must be a JSON object.")

    allowed = {"contract_version", "answers", "scale"}
    unexpected = set(payload) - allowed
    if unexpected:
        raise FSDContractError("Request contains unsupported fields.")

    version = payload.get("contract_version")
    if version != CONTRACT_VERSION:
        raise FSDContractError("Unsupported FSD contract version.")

    answers = payload.get("answers")
    if not isinstance(answers, list) or len(answers) != QUESTION_COUNT:
        raise FSDContractError("Exactly ten answer selections are required.")

    normalized: list[int] = []
    for index, answer in enumerate(answers):
        if isinstance(answer, bool) or not isinstance(answer, int):
            raise FSDContractError(f"Answer {index + 1} must be an integer option index.")
        if answer < OPTION_MIN or answer > OPTION_MAX:
            raise FSDContractError(f"Answer {index + 1} is outside the permitted options.")
        normalized.append(answer)

    scale = payload.get("scale")
    if scale is not None:
        if not isinstance(scale, str) or scale not in SCALES:
            raise FSDContractError("Scale must be one of the supported diagnostic levels.")

    quantum_scores = {}
    for quantum_id, question_indices in QUANTUM_QUESTION_MAP.items():
        values = [normalized[index] for index in question_indices]
        quantum_scores[quantum_id] = {
            "label": PUBLIC_QUANTUM_LABELS[quantum_id],
            "mean_constraint_signal": round(sum(values) / len(values), 3),
            "answered_items": len(values),
        }

    return {
        "contract_version": CONTRACT_VERSION,
        "scale": scale,
        "quantum_summaries": quantum_scores,
        "answer_count": QUESTION_COUNT,
    }


from fsd_question_bank import QUESTIONS as QUESTION_BANK

QUESTION_BANK = tuple({"question": question, "options": options} for question, options in QUESTIONS)
