import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "general_guide_reciprocity_gold_standard.json"
)


def test_reciprocity_gold_standard_is_frozen_and_structurally_complete():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert fixture["benchmark_id"] == "general-guide-reciprocity-gold-standard-2026-10-19"
    assert fixture["status"] == "FROZEN_REFERENCE_ONLY"
    assert fixture["query"] == "What does reciprocity mean in the Living Archive?"

    response = fixture["expected_response"]
    paragraphs = response.split("\n\n")
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("Reciprocity means a relationship of mutual response:")
    assert paragraphs[1].startswith("For example, neighbors might take turns")
    assert "cannot freely offer it" in paragraphs[2]
    assert "debt ledger" in paragraphs[2]

    assert fixture["expected_doorway_title"] == (
        "Reciprocity Before Bureaucracy: How Communities Coordinated Without Modern Institutions"
    )
    assert any("optional" in invariant.lower() for invariant in fixture["invariants"])
    assert any("second click" in invariant.lower() for invariant in fixture["invariants"])
    assert any("provider bank is exhausted" in invariant.lower() for invariant in fixture["invariants"])
    assert any("explicit user authorization" in policy for policy in fixture["freeze_policy"])
    assert any("Do not alter protected use_core.py" in policy for policy in fixture["freeze_policy"])


def test_reciprocity_gold_standard_keeps_source_claims_bounded():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    response = fixture["expected_response"]

    assert "useful starting definition" in response
    assert "linked Archive source may offer a more specific framing" in response
    assert "the canonical definition" not in response.lower()
