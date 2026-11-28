import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
FIXTURE = ROOT / "tests" / "fixtures" / "general-guide-wise-transition-societal-capacities-2026-11-28.json"
BENCHMARK_ID = "general-guide-wise-transition-societal-capacities-2026-11-28"


def test_wise_transition_societal_capacities_response_is_approved_and_frozen():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == BENCHMARK_ID)

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["assistant_assessment_out_of_10"] == 9.5
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    capabilities = record["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["provenance"]["visible_continuation_title"] == fixture["visible_continuation_title"]
    assert "canonical URL" in capabilities["abstention_boundary"]
