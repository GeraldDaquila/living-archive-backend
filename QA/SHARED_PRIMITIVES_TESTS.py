"""Regression probes for the isolated v487.83 shared primitives."""
from __future__ import annotations

from shared_intelligence_primitives import (
    Claim,
    DELEGATE,
    NEEDS_RETRY,
    READY,
    DoorwayCandidate,
    build_epistemic_tag,
    build_synthesis_material,
    normalize_claims,
    normalize_doorway_candidates,
    normalize_evidence,
    operation_result,
    visitor_language_ready,
)


def main() -> int:
    evidence = normalize_evidence(
        [
            {
                "id": "a",
                "title": "Example",
                "url": "https://geralddaquila.com/example/",
                "text": "<p>Source text.</p>",
            },
            {
                "id": "b",
                "title": "Example",
                "url": "https://geralddaquila.com/example/",
                "text": "Duplicate source text.",
            },
            {"title": "Bad", "url": "http://example.com", "text": "Rejected protocol."},
            {"title": "Bad2", "url": "https://", "text": "Rejected malformed URL."},
        ],
        provenance="canonical retrieval",
    )
    assert len(evidence) == 1
    assert evidence[0].text == "Source text."
    assert evidence[0].provenance == "canonical retrieval"

    claims = normalize_claims(
        [
            {
                "text": "A supported proposition.",
                "evidence_ids": ["a"],
                "claim_type": "observation",
                "epistemic": "supported",
                "confidence": 1.4,
            },
            {
                "text": "A supported proposition.",
                "evidence_ids": ["a"],
                "claim_type": "observation",
                "epistemic": "supported",
            },
            {
                "text": "An independent interpretation.",
                "evidence_ids": ["missing"],
                "claim_type": "interpretation",
                "epistemic": "interpretive",
            },
            {
                "text": "An unknown claim type.",
                "evidence_ids": ["a"],
                "claim_type": "not-a-type",
                "epistemic": "not-a-tag",
            },
        ],
        evidence_ids=["a"],
    )
    assert len(claims) == 3
    assert claims[0].evidence_ids == ("a",)
    assert claims[0].confidence == 1.0
    assert claims[1].evidence_ids == ()
    assert claims[1].epistemic == "interpretive"
    assert claims[2].claim_type == "exploration"
    assert claims[2].epistemic == "uncertain"

    assert build_epistemic_tag(supported=True) == "supported"
    assert build_epistemic_tag(inferred=True) == "inferred"
    assert build_epistemic_tag(interpretive=True) == "interpretive"
    assert build_epistemic_tag(visitor_originated=True, supported=True) == "visitor-originated"
    assert build_epistemic_tag(uncertain=True, supported=True) == "uncertain"
    assert build_epistemic_tag() == "uncertain"

    synthesis = build_synthesis_material(
        claims,
        relationship_statement="<p>The claims touch related aspects of the question.</p>",
        unresolved_tensions=["Evidence is incomplete.", "   "],
        perspective_options=["Stay with the source view.", ""],
    )
    assert isinstance(synthesis.claims[0], Claim)
    assert synthesis.source_ids == ("a",)
    assert synthesis.relationship_statement == "The claims touch related aspects of the question."
    assert synthesis.unresolved_tensions == ("Evidence is incomplete.",)
    assert synthesis.perspective_options == ("Stay with the source view.",)

    doorways = normalize_doorway_candidates(
        [
            {
                "title": "<b>A Doorway</b>",
                "url": "https://geralddaquila.com/a-doorway/",
                "relevance_basis": "<p>direct fit</p>",
                "source_ids": ["a"],
                "candidate_rank": "1",
            },
            {
                "title": "A Doorway",
                "url": "https://geralddaquila.com/a-doorway/",
            },
            {"title": "Bad", "url": "http://example.com/"},
        ]
    )
    assert len(doorways) == 1
    assert isinstance(doorways[0], DoorwayCandidate)
    assert doorways[0].title == "A Doorway"
    assert doorways[0].candidate_rank == 1
    assert doorways[0].source_ids == ("a",)

    assert operation_result(READY, mode="general", payload={"ok": True}).status == READY
    assert operation_result(DELEGATE, mode="safety", reason="Specialist route required.").status == DELEGATE
    assert operation_result(NEEDS_RETRY, mode="general", reason="Evidence unavailable.").status == NEEDS_RETRY

    failed = False
    try:
        operation_result(READY, mode="general")
    except ValueError:
        failed = True
    assert failed

    failed = False
    try:
        operation_result(NEEDS_RETRY, mode="general")
    except ValueError:
        failed = True
    assert failed

    assert visitor_language_ready("This is a human-readable answer.")
    assert not visitor_language_ready("OperationResult(status=READY)")
    assert not visitor_language_ready("EvidenceItem(id='a')")
    assert not visitor_language_ready("")

    print("v487.83 shared primitives regression probes: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
