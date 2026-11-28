import json
from pathlib import Path

import nonprofit_mission_care_contract as contract

ROOT = Path(__file__).resolve().parents[1]
NEAR_MISS = ROOT / "tests/fixtures/general-guide-nonprofit-mission-care-compressed-nearmiss-2026-11-28.json"
SUCCESSOR = ROOT / "tests/fixtures/general-guide-nonprofit-mission-care-operational-capacity-doorway-2026-11-28.json"


def test_second_live_compressed_answer_is_preserved_as_nearmiss():
    item = json.loads(NEAR_MISS.read_text(encoding="utf-8"))
    assert item["status"] == "PRESERVED_NEAR_MISS"
    assert item["doorway_title"] == "Infrastructure Before Ideology"
    assert "performance expectations and compensation" in item["original_response"]


def test_successor_completes_operational_sequence_and_actionable_doorway():
    item = json.loads(SUCCESSOR.read_text(encoding="utf-8"))
    answer = item["expected_response"].casefold()
    assert item["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert item["runtime_transfer"] is False
    assert item["gold_star_capabilities"]["exact_answer_authority"] is False
    assert item["gold_star_capabilities"]["active_quality_contributor"] is False
    for phrase in ("essential mission commitments", "without retaliation", "hidden work", "stabilize immediate overload", "stop, defer, simplify, redistribute, fund, or phase", "governance", "staff depletion is not a reserve resource", "one-page capacity-and-commitment map"):
        assert phrase in answer
    assert item["doorway_status"] == "NOT_EVALUATED"
    assert item["expected_doorway"] is None
    assert "capacity-and-commitment map" in item["expected_next_step"]


def test_question_contract_is_narrow_and_excludes_adjacent_questions():
    q = "A nonprofit is mission-driven but burning out its staff. How should the Guide connect care, structure, purpose, and operational reality?"
    assert contract.is_nonprofit_mission_care_question(q)
    assert "capacity-and-commitment map" in contract.build_nonprofit_mission_care_instruction(q)
    assert not contract.is_nonprofit_mission_care_question("What is the history of nonprofit organizations?")
    assert not contract.is_nonprofit_mission_care_question("How can a company improve staff morale?")
    assert contract.build_nonprofit_mission_care_instruction("What is the history of nonprofit organizations?") == ""


def test_nonprofit_contract_is_injected_into_actual_provider_system_message():
    import general_guide_composition as composition
    question = "A nonprofit is mission-driven but burning out its staff. How should the Guide connect care, structure, purpose, and operational reality?"
    message = composition._build_general_guide_system_message(question)
    assert "NONPROFIT MISSION-CARE OPERATIONAL COMPLETION" in message
    assert "capacity-and-commitment map" in message


def test_nonprofit_contract_does_not_capture_unrelated_questions():
    import general_guide_composition as composition
    message = composition._build_general_guide_system_message("What is the history of nonprofit organizations?")
    assert "NONPROFIT MISSION-CARE OPERATIONAL COMPLETION" not in message


def test_successor_fixture_reconciles_to_canonical_registry():
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    fixture = json.loads(SUCCESSOR.read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] == fixture["expected_doorway"]
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    assert record["runtime_transfer"] is False
    assert record["numbering_status"] == "UNASSIGNED"


def test_trust_centered_screenshot_is_preserved_as_a_distinct_nearmiss():
    item = json.loads((ROOT / "tests/fixtures/general-guide-nonprofit-mission-care-trust-centered-nearmiss-2026-11-28.json").read_text(encoding="utf-8"))
    assert item["status"] == "PRESERVED_NEAR_MISS"
    assert "trust erodes" in item["original_response"]
    assert "human energy as an unlimited resource" in item["original_response"]
    assert item["visible_continuation_title"] == "Infrastructure Before Ideology"


def test_trust_centered_successor_is_operationally_complete_and_registry_frozen():
    fixture = json.loads((ROOT / "tests/fixtures/general-guide-nonprofit-mission-care-trust-centered-gold-star-2026-11-28.json").read_text(encoding="utf-8"))
    answer = fixture["expected_response"].casefold()
    assert fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    for phrase in ("human capacity", "without retaliation", "trust-centered structure", "incentives", "hidden work", "stop, defer, simplify, redistribute, fund, or phase", "staff and governance", "capacity-and-commitment review"):
        assert phrase in answer
    assert fixture["runtime_transfer"] is False
    assert fixture["gold_star_capabilities"]["exact_answer_authority"] is False
    assert fixture["gold_star_capabilities"]["active_quality_contributor"] is False
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert record["expected_response"] == fixture["expected_response"]
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None


def test_trust_centered_screenshot_is_preserved_as_a_distinct_nearmiss():
    item = json.loads((ROOT / "tests/fixtures/general-guide-nonprofit-mission-care-trust-centered-nearmiss-2026-11-28.json").read_text(encoding="utf-8"))
    assert item["status"] == "PRESERVED_NEAR_MISS"
    assert "trust erodes" in item["original_response"]
    assert "human energy as an unlimited resource" in item["original_response"]
    assert item["visible_continuation_title"] == "Infrastructure Before Ideology"


def test_trust_centered_successor_is_operationally_complete_and_registry_frozen():
    fixture = json.loads((ROOT / "tests/fixtures/general-guide-nonprofit-mission-care-trust-centered-gold-star-2026-11-28.json").read_text(encoding="utf-8"))
    answer = fixture["expected_response"].casefold()
    assert fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    for phrase in ("human capacity", "without retaliation", "trust-centered structure", "incentives", "hidden work", "stop, defer, simplify, redistribute, fund, or phase", "staff and governance", "capacity-and-commitment review"):
        assert phrase in answer
    assert fixture["runtime_transfer"] is False
    assert fixture["gold_star_capabilities"]["exact_answer_authority"] is False
    assert fixture["gold_star_capabilities"]["active_quality_contributor"] is False
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert record["expected_response"] == fixture["expected_response"]
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
