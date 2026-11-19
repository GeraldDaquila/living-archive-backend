# Gold Star v2 — Trust / Community Stewardship Reference

**Benchmark ID:** `gold-star-v2-trust-community-stewardship-2026-11-19`  
**Status:** FROZEN REFERENCE CANDIDATE  
**Visitor query:** “What is the role of trust in community stewardship?”  
**Observed:** 2026-11-19, live Guide, after both production services reported the Gold Star answer elevation merge commit live.

## Why this reference is retained

The visitor-facing answer demonstrates the intended Guide experience in one compact interaction:

1. Receive a human question and answer it directly.
2. Explain the underlying concept through observable conduct rather than abstract slogans.
3. Translate the idea into a recognizable community example.
4. Move from explanation to practical accountability and repair.
5. Preserve important distinctions and safeguards.
6. Offer a relevant Living Archive doorway as optional continuation, not as a substitute for the answer.

## Frozen response and contract

The canonical expected response is stored in:

`tests/fixtures/gold_star_v2_trust_community_stewardship.json`

The visitor contract regression test compares the complete response against that fixture and verifies the answer basis and separate Archive recommendation:

`tests/test_guide_trust_community_stewardship_recovery.py`

The expected answer basis is `general_knowledge` / “Conceptual explanation”. The Trust Architecture essay is a separate `archive_resource` recommendation. It must not be represented as the evidence source for the conceptual explanation.

## Acceptance invariants

- Trust is explained as confidence built through observable conduct.
- Shared responsibility is explained without implying constant supervision.
- The shared-garden example makes the idea concrete.
- Accountability includes naming what happened, listening to impact, agreeing on repair, and clarifying responsibilities.
- Trust, accountability, and stewardship remain distinct but connected.
- Trust is not treated as a replacement for scrutiny or safeguards.
- The answer is complete before optional navigation appears.
- The Archive recommendation remains separate from the answer's provenance.
- A single Search submission is sufficient to render the answer.

## Change control

This is a separately versioned Gold Star v2 reference. It does not replace or modify the frozen 2026-10-14 General Purpose Guide benchmark.

Do not edit the expected response to make a failing regression pass. Any replacement requires explicit authorization, a new benchmark version, and a documented reason. Preserve this fixture as the historical reference.

## Evidence and limits

The user supplied a live visitor-facing screenshot on 2026-11-19. The screenshot establishes the visible answer and doorway. The backend contract and existing regression checks establish the expected provenance and recommendation separation. The fixture now locks those expectations for automated regression.

The screenshot itself is not stored in the repository by this change. This benchmark does not certify the whole Guide, prove quality across unrelated question classes, or replace independent human calibration. Automated tests verify repeatability and contract integrity; independent human review remains a separate acceptance gate.
