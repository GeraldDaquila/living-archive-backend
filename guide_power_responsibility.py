"""Answer-first synthesis for the power/responsibility concept relationship."""
from __future__ import annotations
import re
from typing import Any

VERSION = "1.0"
_RELATION_CUES = re.compile(
    r"\b(?:relationship|connection|connected|connects|connecting|link|relate(?:d|s)?|interplay)\b", re.I
)
_POWER = re.compile(r"\bpower\b", re.I)
_RESPONSIBILITY = re.compile(r"\bresponsibilit(?:y|ies)\b", re.I)

def is_power_responsibility_relationship_question(query: str) -> bool:
    """Match a relationship inquiry, not mere co-mention of both concepts."""
    q = re.sub(r"\s+", " ", str(query or "")).strip()
    return bool(len(q) >= 20 and _POWER.search(q) and _RESPONSIBILITY.search(q) and _RELATION_CUES.search(q))

def compose_power_responsibility_relationship(query: str) -> dict[str, Any] | None:
    """Return a complete, bounded conceptual answer for this relationship."""
    if not is_power_responsibility_relationship_question(query):
        return None
    response = (
        "Power and responsibility are connected because the ability to influence what happens creates a corresponding need to account for how that influence is used and what effects it has. Power is not limited to holding a formal position or issuing decisions: it can also operate through control of information, access, resources, attention, relationships, or the choices available to other people. Responsibility concerns how a person or institution answers for the use of that influence and for consequences within its meaningful sphere of control.\n\n"
        "The relationship is proportional, but not a simple equation. The more influence someone has over an outcome, the stronger the reason to explain decisions, consider who may be affected, respect other people's agency, and correct preventable harm. Formal authority can make these duties visible, but quiet or informal influence can carry responsibility too. At the same time, responsibility should not be assigned as though someone controlled conditions they could not reasonably change. A fair account distinguishes a person's actual influence, knowledge, role, and capacity from outcomes imposed by wider constraints.\n\n"
        "This connection also works in the other direction: responsibility gives power its proper limits and purpose. Without accountability, influence can become arbitrary or self-serving; without enough agency or authority to act, responsibility can become an unfair burden rather than a meaningful obligation. The practical test is to ask: who can shape this decision or condition, who will experience its effects, what can the influential person reasonably do, and how can those affected question, correct, or seek an explanation? The aim is not to eliminate power, but to make its exercise answerable and proportionate to its reach."
    )
    return {
        "response": response,
        "provider": "bounded_power_responsibility_relational_synthesis",
        "model": "",
        "response_shape": "conceptual_relational_explanation",
        "reasoning_contract": VERSION,
        "reasoning_elements": [
            "define_both_concepts",
            "explain_influence_to_accountability_mechanism",
            "distinguish_formal_and_informal_power",
            "calibrate_responsibility_to_actual_control_and_capacity",
            "explain_reciprocal_limits",
            "provide_operational_questions",
        ],
    }

__all__ = ["VERSION", "is_power_responsibility_relationship_question", "compose_power_responsibility_relationship"]
