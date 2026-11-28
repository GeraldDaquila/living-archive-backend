import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "general-guide-nonprofit-mission-care-operational-capacity-2026-11-28.json"
BENCHMARK_ID = "general-guide-nonprofit-mission-care-operational-capacity-2026-11-28"


def test_nonprofit_mission_care_operational_capacity_successor_is_complete_and_bounded():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = fixture["expected_response"].lower()

    assert fixture["benchmark_id"] == BENCHMARK_ID
    assert fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert fixture["query"] == "A nonprofit is mission-driven but burning out its staff. How should the Guide connect care, structure, purpose, and operational reality?"
    assert fixture["assistant_assessment_out_of_10"] == 9.7
    assert fixture["runtime_transfer"] is False
    capabilities = fixture["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False

    for phrase in (
        "purpose:",
        "care:",
        "structure:",
        "operational reality:",
        "governance",
        "stop, defer, simplify, redistribute, fund, or phase",
        "without retaliation",
        "hidden work",
        "absence or turnover",
        "stabilizing immediate overload",
        "review whether workload",
        "staff depletion as the missing resource",
    ):
        assert phrase in answer

    assert "not an individual failure" in answer
    assert "not an assumption about every nonprofit" in answer
    assert fixture["doorway_status"] == "NOT_EVALUATED"  # Earlier approved baseline remains unchanged.
    assert fixture["expected_doorway"] is None  # Earlier baseline's doorway remains unevaluated.
    assert fixture["visible_continuation_title"] == "Infrastructure Before Ideology"
    assert "no canonical url is inferred" in capabilities["abstention_boundary"].lower()
    assert "issue #2177" in fixture["provenance"]["original_near_miss"]
