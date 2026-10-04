"""v487.94 Stewardship Formation specialist pipe QA."""

from formation_adapter import FormationAdapter
from formation_contribution import (
    FORMATION_CONTRIBUTION_CONTRACT_VERSION,
    validate_formation_contribution,
)
from specialist_adapters import SpecialistAdapterContext


def run() -> None:
    adapter = FormationAdapter()
    context = SpecialistAdapterContext(
        request_id="qa-formation-001",
        guide_version="v487.90",
        specialist_id="formation",
        original_question="I am taking on a larger responsibility and need to understand how to carry it well.",
        recognized_territory="stewardship formation",
        processing_purpose="bounded formation navigation",
        guide_context={
            "situation": "I am taking on a larger responsibility and need to know how to carry it well.",
            "possibility": "I want to become more steady without making everything depend on me.",
        },
        safety_state="green",
    )
    contribution = validate_formation_contribution(adapter.process(context))

    assert contribution["contract_version"] == FORMATION_CONTRIBUTION_CONTRACT_VERSION
    assert contribution["status"] == "CONTRIBUTION"
    assert contribution["movement"]["direction"] == "formation"

    doors = contribution["canonical_candidates"]
    assert 1 <= len(doors) <= 3
    assert len({door["id"] for door in doors}) == len(doors)
    assert all(door["url"].startswith("https://geralddaquila.com/") for door in doors)
    assert all(
        door["id"] not in {"stewardship_archive", "canonical_writings", "constitutional_architecture"}
        for door in doors
    )

    interpretation = contribution["interpretation"]
    assert interpretation["signals"]["responsibility_transition"] is True
    assert interpretation["signals"]["practice"] is False

    print("v487.94 Formation specialist pipe QA: PASS")


if __name__ == "__main__":
    run()
