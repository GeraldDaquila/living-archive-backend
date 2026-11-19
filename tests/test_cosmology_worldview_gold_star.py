"""Frozen Gold Star contract for cosmology, worldview, and human life."""

import asyncio
import json
from pathlib import Path

import main
import general_guide_composition as composition
from general_guide_gold_standards import resolve_exact_gold_standard


ROOT = Path(__file__).resolve().parents[1]
QUERY = "What is cosmology, and why does it matter to how people live?"
BENCHMARK_ID = "gs-2026-11-19-cosmology-worldview-human-life"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "cosmology_worldview_human_life_gold_star.json"
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"
DOORWAY_URL = "https://geralddaquila.com/2026/08/09/constitutional-ontology-hidden-maps/"
DOORWAY_TITLE = "The Hidden Assumptions That Quietly Shape Every Life"


def test_live_cosmology_question_resolves_to_the_approved_gold_star():
    record = resolve_exact_gold_standard(QUERY)
    assert record is not None
    assert record["benchmark_id"] == BENCHMARK_ID
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["doorway_title"] == DOORWAY_TITLE
    assert record["doorway_url"] == DOORWAY_URL
    assert record["forbids_doorway"] is False


def test_registered_exact_answer_and_doorway_match_the_frozen_browser_fixture():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    records = [item for item in registry["records"] if item.get("benchmark_id") == BENCHMARK_ID]
    assert len(records) == 1
    record = records[0]
    assert record["query"] == fixture["query"] == QUERY
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] == fixture["expected_doorway"]
    assert record["rating_out_of_10"] == 9.2
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"


def test_deterministic_composition_returns_the_exact_frozen_answer_and_doorway():
    result = composition.compose(use_core=None, query=QUERY, context_data={})
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert result is not None
    assert result["provider"] == "gold_standard_registry"
    assert result["model"] == "approved-reference"
    assert result["response"] == fixture["expected_response"]
    assert result["doorway_title"] == DOORWAY_TITLE
    assert result["doorway_url"] == DOORWAY_URL


def test_final_visitor_boundary_overrides_stale_provider_answer_and_doorway():
    result = main._guide_finalize_visitor_payload(
        {
            "ok": True,
            "response": "A generic answer that does not meet the approved standard.",
            "recommendation": {
                "title": "Living Glossary",
                "url": "https://geralddaquila.com/glossary/",
                "rationale": "A generic fallback that is not the approved continuation.",
            },
        },
        QUERY,
    )
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert result["response"] == fixture["expected_response"]
    assert result["recommendation"]["title"] == DOORWAY_TITLE
    assert result["recommendation"]["url"] == DOORWAY_URL
    assert result["canonical_doorway"]["title"] == DOORWAY_TITLE
    assert result["canonical_doorway"]["url"] == DOORWAY_URL


def test_universal_json_sender_preserves_the_exact_gold_star_and_doorway():
    messages = []
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload = {
        "ok": True,
        "query": QUERY,
        "response": "A stale provider answer.",
        "recommendation": {
            "title": "Living Glossary",
            "url": "https://geralddaquila.com/glossary/",
        },
    }

    async def fake_send(message):
        messages.append(message)

    asyncio.run(main._use_send_json(fake_send, payload))
    body = json.loads(messages[-1]["body"].decode("utf-8"))
    assert body["response"] == fixture["expected_response"]
    assert body["recommendation"]["title"] == DOORWAY_TITLE
    assert body["recommendation"]["url"] == DOORWAY_URL
    assert body["canonical_doorway"]["title"] == DOORWAY_TITLE
    assert body["canonical_doorway"]["url"] == DOORWAY_URL


def test_scientific_cosmology_and_adjacent_worldview_questions_are_not_captured():
    for query in (
        "What is scientific cosmology?",
        "How does the universe expand?",
        "What is a worldview?",
        "How do inherited assumptions shape institutions?",
    ):
        assert resolve_exact_gold_standard(query) is None


def test_cosmology_gold_star_has_a_matching_bounded_transfer_review():
    review = json.loads(
        (ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(
            encoding="utf-8"
        )
    )
    entries = [item for item in review["entries"] if item.get("benchmark_id") == BENCHMARK_ID]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["reasoning_family"] == "cosmology_worldview_human_life"
    assert entry["activation"] == "active_quality_contributor"
    assert "scientific cosmology" in entry["transferable_discipline"]
    assert "ordinary astronomy" in entry["abstention_boundary"]
