"""Integrity checks for the human-discernment Gold Star doorway amendment."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / "docs" / "qa" / "human_discernment_doorway_transition_amendment.json"


def test_doorway_transition_is_explanatory_not_a_bare_label():
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    transition = amendment["doorway_transition"]
    assert transition.startswith("To explore the wider implications of this practice,")
    assert "continue with the related Living Archive resource" in transition
    assert "Truth in the Age of AI: Why Discernment Is Becoming a Survival Skill" in transition
    assert "Doorway:" not in transition


def test_near_miss_and_successor_remain_distinct_and_frozen():
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    assert amendment["benchmark_id"] == "general-guide-human-discernment-ai-governance-2026-11-28"
    assert amendment["linked_near_miss_benchmark_id"] == "general-guide-human-discernment-ai-support-near-miss-2026-11-28"
    assert "Preserve the original visitor response unchanged" in amendment["integrity_rules"][0]
    assert "Keep the successor separate from the near-miss" in amendment["integrity_rules"][1]


def test_doorway_evidence_boundary_does_not_invent_destination_or_runtime_claims():
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    assert amendment["doorway_status"] == "TITLE_VISIBLE_IN_USER_SUPPLIED_SCREENSHOT; CANONICAL_URL_NOT_INDEPENDENTLY_VERIFIED"
    assert "does not invent a URL" in amendment["evidence_boundary"]
    assert any("runtime/adaptive transfer" in rule for rule in amendment["integrity_rules"])
