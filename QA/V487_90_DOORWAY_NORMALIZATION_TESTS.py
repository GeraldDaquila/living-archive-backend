"""Focused compatibility probes for the v487.90 doorway normalization primitive."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared_intelligence_primitives import DoorwayCandidate, normalize_doorway_candidates

def main():
    candidates = normalize_doorway_candidates([
        {"title": "<b>First</b>", "url": "https://geralddaquila.com/first/", "relevance_basis": "<p>subject</p>", "source_ids": ["doc-a", ""]},
        {"title": "Duplicate", "url": "https://geralddaquila.com/first", "candidate_rank": "9"},
        {"title": "Second", "canonical_url": "https://geralddaquila.com/second/", "source_ids": ["doc-b"]},
        {"title": "HTTP", "url": "http://example.org/", "source_ids": ["bad"]},
        {"title": "", "url": "https://example.org/empty/"},
        "not-a-candidate",
    ])
    assert candidates == (
        DoorwayCandidate(title="First", url="https://geralddaquila.com/first/", relevance_basis="subject", source_ids=("doc-a",), candidate_rank=1),
        DoorwayCandidate(title="Second", url="https://geralddaquila.com/second/", relevance_basis="", source_ids=("doc-b",), candidate_rank=10),
    )

    untouched = normalize_doorway_candidates([
        {"title": "Explicit", "url": "https://geralddaquila.com/explicit/", "candidate_rank": 4},
        {"title": "Next", "url": "https://geralddaquila.com/next/"},
    ])
    assert [item.candidate_rank for item in untouched] == [4, 5]
    assert all(isinstance(item, DoorwayCandidate) for item in untouched)

    print("v487.90 doorway normalization compatibility probes: PASS")

if __name__ == "__main__":
    main()
