"""Structural regression: provenance labels cannot erase verified Guide navigation."""
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")


def test_archive_claim_boundary_preserves_or_recovers_navigation():
    start = MAIN.index("if _is_archive_claim_boundary_inquiry(query):")
    end = MAIN.index("# Comparative and contextual synthesis", start)
    block = MAIN[start:end]
    assert "_boundary_canonical_doorway(safe, query)" in block
    assert "registered_recovery_recommendation" in block
    assert 'safe["recommendation"] = _archive_doorway' in block


def test_json_sender_does_not_exempt_provenance_processing_from_navigation():
    start = MAIN.index("async def _use_send_json")
    block = MAIN[start:start + 9000]
    assert "_forbids_doorway" in block
    assert "not _archive_claim_final" not in block
    assert "Only an explicit canonical forbids_doorway instruction" in block
