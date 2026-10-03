"""Production Stewardship Formation specialist adapter.

This is a bounded micro-navigator, not a second USE. Its intelligence is
derived from the established Stewardship Pathway v0.9 mechanism: situation +
desired movement -> structured signals -> three coherent canonical doors.

No provider call is required for this bounded MVP. The adapter returns
structured material to The Guide, which remains responsible for final
integration and presentation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Mapping

from specialist_adapters import SpecialistAdapter, SpecialistAdapterContext
from formation_contribution import (
    FORMATION_VOICE_POLICY,
    validate_formation_contribution,
)


FORMATION_RESOURCES = (
    {
        "id": "learning_arcs",
        "title": "Learning Arcs",
        "url": "https://geralddaquila.com/steward-access-12-learning-arcs/",
        "function": ("develop", "continue", "integrate"),
    },
    {
        "id": "stewardship_frameworks",
        "title": "Stewardship Frameworks",
        "url": "https://geralddaquila.com/stewardship-framework/",
        "function": ("orient", "develop"),
    },
    {
        "id": "stewardship_practice",
        "title": "Stewardship Practice",
        "url": "https://geralddaquila.com/stewardship-practice/",
        "function": ("practice", "integrate"),
    },
    {
        "id": "governance_foundations",
        "title": "Governance Foundations",
        "url": "https://geralddaquila.com/governance-foundations/",
        "function": ("develop", "practice", "ground"),
    },
)


class FormationAdapter(SpecialistAdapter):
    specialist_id = "formation"

    @staticmethod
    def _signals(text: str) -> Dict[str, bool]:
        value = str(text or "").casefold()
        return {
            "responsibility_transition": bool(re.search(
                r"\b(?:change|changing|transition|new role|next|growing|growth|handover|"
                r"succession|delegate|responsib\w*|founder|legacy|inherit)\b", value
            )),
            "continuity": bool(re.search(
                r"\b(?:continu\w*|legacy|inherit\w*|future|long.?term|preserv\w*|"
                r"carry forward|succession|next generation)\b", value
            )),
            "institution_building": bool(re.search(
                r"\b(?:company|organization|institution|business|grow\w*|structure|"
                r"system|scale|build\w*)\b", value
            )),
            "shared_responsibility": bool(re.search(
                r"\b(?:team|people|others|together|shared|council|community|delegate|"
                r"participat\w*|staff)\b", value
            )),
            "governance": bool(re.search(
                r"\b(?:govern\w*|authority|decision|institution|structure|policy|"
                r"accountab\w*|council|rules|law|leadership)\b", value
            )),
            "practice": bool(re.search(
                r"\b(?:practice|act|doing|implement|apply|build|work|tool|capable|"
                r"execute)\b", value
            )),
            "formation_ground": bool(re.search(
                r"\b(?:principle\w*|purpose|meaning|responsibility|stewardship|power|"
                r"sovereignty|consent|authority|coherence|human flourishing)\b", value
            )),
        }

    @staticmethod
    def _pathway(signals: Mapping[str, bool]) -> str:
        if (
            signals["responsibility_transition"]
            and signals["continuity"]
            and signals["institution_building"]
        ):
            return (
                "You seem to be holding two responsibilities at once: honoring what "
                "has brought this situation here, while allowing it to become something "
                "that can grow beyond one person's way of doing things. The question is "
                "therefore larger than transition alone. It is also about what should "
                "remain, what can change, and what will be needed to carry the purpose "
                "into its next chapter."
            )
        if signals["continuity"]:
            return (
                "The question seems to be about continuity: how to carry something that "
                "matters forward without turning the past into a script for the future."
            )
        if signals["responsibility_transition"]:
            return (
                "Something about the responsibility you are carrying is changing. The "
                "question may not be how to do more, but how to carry it differently as "
                "the situation grows or changes around you."
            )
        if signals["institution_building"] or signals["governance"]:
            return (
                "What you have described reaches beyond a single decision. It touches "
                "the way responsibility, authority, and continuity are held when other "
                "people and structures begin to matter more."
            )
        if signals["practice"]:
            return (
                "You are looking for movement, not just understanding. The question is "
                "how something that matters can become part of what you actually do."
            )
        return (
            "You have brought a real situation, but you do not need to settle its "
            "meaning before you begin. The Stewardship work has several places where "
            "the question can be held open and examined from another angle."
        )

    @staticmethod
    def _door_ids(signals: Mapping[str, bool]):
        doors = []
        if signals["responsibility_transition"] or signals["continuity"]:
            doors.append("learning_arcs")
        else:
            doors.append("stewardship_frameworks")

        if signals["institution_building"] or signals["governance"] or signals["shared_responsibility"]:
            doors.append("governance_foundations")
        elif signals["practice"]:
            doors.append("stewardship_practice")
        else:
            doors.append("stewardship_frameworks")

        if signals["practice"] and not signals["institution_building"]:
            doors.append("stewardship_practice")
        elif signals["continuity"] or signals["formation_ground"]:
            doors.append("learning_arcs")
        else:
            doors.append("stewardship_frameworks")

        unique = []
        for item in doors:
            if item not in unique:
                unique.append(item)
        return unique[:3]

    def process(self, context: SpecialistAdapterContext) -> Mapping[str, Any]:
        guide_context = dict(context.guide_context or {})
        situation = str(
            guide_context.get("situation")
            or context.original_question
            or ""
        ).strip()
        possibility = str(
            guide_context.get("possibility")
            or guide_context.get("desired_movement")
            or ""
        ).strip()

        combined = f"{situation} {possibility}".strip()
        signals = self._signals(combined)
        door_ids = self._door_ids(signals)
        by_id = {item["id"]: item for item in FORMATION_RESOURCES}
        doors = [by_id[item] for item in door_ids if item in by_id]

        contribution = {
            "contract_version": "v1",
            "request_id": context.request_id,
            "specialist_id": self.specialist_id,
            "status": "CONTRIBUTION",
            "voice_policy": FORMATION_VOICE_POLICY,
            "interpretation": {
                "situation": situation,
                "movement": possibility,
                "signals": signals,
                "pathway": self._pathway(signals),
            },
            "perspectives": [],
            "movement": {
                "direction": "formation",
                "next_horizon": (
                    "recognize what this situation may be asking the visitor "
                    "to learn, practice, examine, or carry"
                ),
                "door_count": len(doors),
            },
            "canonical_candidates": doors,
            "boundary_notes": {
                "t4_destination_allowed": False,
                "diagnostic_claim": False,
                "source_mechanism": "stewardship-pathway-v0.9",
            },
            "safety_flags": {
                "safety_state": context.safety_state,
            },
        }
        return validate_formation_contribution(contribution)
