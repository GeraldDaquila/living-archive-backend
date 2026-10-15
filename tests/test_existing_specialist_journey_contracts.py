"""Cross-boundary regressions for the existing Guide specialist contracts.

These tests compose the already-established hub, adapter pipe, and specialist
domain contracts. They deliberately do not introduce a new response envelope
or exercise live providers/WordPress; live visitor journeys remain a separate
end-to-end gate.
"""

from hub_contracts import build_hub_request, route_spoke
from formation_adapter import FormationAdapter
from relationship_contribution import RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION
from specialist_adapters import (
    SpecialistAdapterRegistry,
    invoke_specialist,
)


class CalibratedRelationshipFixture:
    """Contract fixture for the calibrated HRN domain contribution."""

    specialist_id = "relationship"

    def process(self, context):
        assert context.original_question == (
            "Two colleagues disagree about how responsibility should be shared."
        )
        return {
            "contract_version": RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
            "status": "CONTRIBUTION",
            "voice_policy": "preserve_specialist_voice",
            "human_response": "The disagreement may be carrying different expectations of responsibility.",
            "interpretation": {"focus": "shared responsibility"},
            "perspectives": [{"view": "colleague_a"}, {"view": "colleague_b"}],
            "movement": {"question": "What does each person believe they are responsible for?"},
            "canonical_candidates": [
                {"title": "Stewardship Framework", "url": "https://geralddaquila.com/stewardship-framework/"}
            ],
            "journey": {"journey_state": "in_progress", "unit_turns": 1},
        }


def _invoke_through_existing_seams(registry, request, specialist_id):
    def invoke(**kwargs):
        return invoke_specialist(
            registry,
            request_id=kwargs["request_id"],
            guide_version=kwargs["guide_version"],
            specialist_id=kwargs["specialist_id"],
            original_question=kwargs["original_question"],
            recognized_territory=kwargs["recognized_territory"],
            processing_purpose=kwargs["processing_purpose"],
            guide_context=kwargs["guide_context"],
            safety_state=kwargs["safety_state"],
        )

    return route_spoke(
        request=request,
        specialist_id=specialist_id,
        invoke=invoke,
    )


def test_relationship_domain_payload_survives_adapter_pipe_and_hub():
    registry = SpecialistAdapterRegistry()
    registry.register(CalibratedRelationshipFixture())
    request = build_hub_request(
        request_id="integration-hrn-001",
        guide_version="test",
        original_question=(
            "Two colleagues disagree about how responsibility should be shared."
        ),
        recognized_territory="human relationships",
        processing_purpose="open relational exploration",
        guide_context={"conversation": "prior turn context"},
        safety_state="green",
    )

    result = _invoke_through_existing_seams(registry, request, "relationship")

    assert result.request_id == "integration-hrn-001"
    assert result.specialist_id == "relationship"
    assert result.payload["voice_policy"] == "preserve_specialist_voice"
    assert result.payload["contract_version"] == RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION
    assert result.payload["human_response"].startswith("The disagreement may be carrying")
    assert result.payload["movement"]["question"].startswith("What does each person")
    assert result.payload["journey"]["journey_state"] == "in_progress"
    assert result.payload["perspectives"] == [
        {"view": "colleague_a"}, {"view": "colleague_b"}
    ]
    assert result.canonical_candidates[0]["title"] == "Relationship Door"


def test_formation_three_doors_survive_adapter_pipe_and_hub():
    registry = SpecialistAdapterRegistry()
    registry.register(FormationAdapter())
    situation = (
        "I have taken on a larger responsibility and want to understand how "
        "to carry it without making everything depend on me."
    )
    possibility = "I hope to become more steady and share responsibility in practice."
    request = build_hub_request(
        request_id="integration-formation-001",
        guide_version="test",
        original_question=situation,
        recognized_territory="stewardship formation",
        processing_purpose="bounded formation navigation",
        guide_context={
            "choice": "carrying",
            "situation": situation,
            "possibility": possibility,
        },
        safety_state="green",
    )

    result = _invoke_through_existing_seams(registry, request, "formation")

    assert result.request_id == "integration-formation-001"
    assert result.specialist_id == "formation"
    assert result.payload["voice_policy"] == "preserve_specialist_boundary"
    assert result.payload["contract_version"] == "formation-v1"
    assert len(result.canonical_candidates) == 3
    assert len({door["id"] for door in result.canonical_candidates}) == 3
    assert all(door["url"].startswith("https://geralddaquila.com/") for door in result.canonical_candidates)
    assert result.payload["interpretation"]["situation"] == situation
    assert result.payload["movement"]["door_count"] == 3
