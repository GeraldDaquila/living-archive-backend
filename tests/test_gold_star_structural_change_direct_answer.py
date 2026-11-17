import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import active_quality_contribution, deterministic_fallback_contribution

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
BENCHMARK_ID = "gs-2026-11-17-structural-change-vs-disruption"
QUESTION = "How can one distinguish structural change from ordinary disruption?"


def test_structural_change_answer_is_restored_with_verified_canonical_doorway():
    record = next(r for r in REGISTRY["records"] if r["benchmark_id"] == BENCHMARK_ID)
    paragraphs = record["expected_response"].split("\\n\\n")
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert len(paragraphs) == 3
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"]["title"] == "Systems, Governance, and Organizational Design"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/systems-structure/"
    assert record["expected_doorway"]["rationale"]
    assert record["expected_response"].startswith("Structural change reorganizes the arrangements")
    assert "The test is not simply whether something new happened" in record["expected_response"]
    assert record["withdrawal"]["resolved_at"] == "2026-11-17"
    assert record["reinstatement"]["destination_post_id"] == 41615


def test_structural_change_gold_star_resolves_exact_answer_and_doorway_rationale():
    result = resolve_exact_gold_standard(QUESTION)
    assert result is not None
    assert result["benchmark_id"] == BENCHMARK_ID
    assert result["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert result["doorway_title"] == "Systems, Governance, and Organizational Design"
    assert result["doorway_url"] == "https://geralddaquila.com/systems-structure/"
    assert result["doorway_rationale"] == "This hub examines how underlying structures, incentives, governance arrangements, and complexity shape system behavior—the wider context for judging whether a change alters the conditions that reproduce outcomes."


def test_structural_change_gold_star_contributes_bounded_discipline_only():
    related = "How can one distinguish structural change from ordinary disruption in an organization?"
    active = active_quality_contribution(related)
    deterministic = deterministic_fallback_contribution(related)
    assert active is not None
    assert active["benchmark_id"] == BENCHMARK_ID
    assert active["authority_mode"] == "structural_guidance_only"
    assert deterministic is not None
    assert deterministic["benchmark_id"] == BENCHMARK_ID
    assert deterministic["authority_mode"] == "deterministic_structural_guidance_only"


def test_frontend_renders_registry_authored_doorway_rationale():
    source = (ROOT / "wordpress" / "living-archive-guide-v489.318-edge-confirmation.js").read_text(encoding="utf-8")
    assert "recommendation.rationale" in source
    assert "archive-recommendation-rationale" in source
