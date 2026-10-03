"""Compatibility probes for the v487.91 doorway normalization adapter."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import _build_doorway_candidates_for_use
from shared_intelligence_primitives import DoorwayCandidate

def main():
    result = _build_doorway_candidates_for_use([
        {"title": "<b>Door</b>", "canonical_url": "https://geralddaquila.com/door/", "relevance_basis": "<p>context</p>", "source_ids": ["a", ""]},
        {"title": "Dup", "url": "https://geralddaquila.com/door"},
        {"title": "Next", "url": "https://geralddaquila.com/next/"}
    ])
    assert isinstance(result, tuple)
    assert all(isinstance(item, DoorwayCandidate) for item in result)
    assert [item.title for item in result] == ["Door", "Next"]
    assert [item.candidate_rank for item in result] == [1, 2]
    assert result[0].relevance_basis == "context"
    assert result[0].source_ids == ("a",)
    assert _build_doorway_candidates_for_use([]) == ()
    print("v487.91 doorway adapter compatibility probes: PASS")
if __name__ == "__main__":
    main()
