# v487.80 Shared Contract Validation

This checkpoint establishes the minimum shared vocabulary before any runtime abstraction is created.

## Current contract set

**EvidenceItem** keeps source passages and provenance distinct.

**Claim** keeps a complete proposition tied to supporting evidence and an explicit claim/epistemic type.

**InquiryMovement** accommodates both USE's macro interpretation and HRN's conversational movement
without forcing either into a shared domain-specific state machine.

**EpistemicTag** distinguishes supported, inferred, interpretive, visitor-originated, and uncertain
material.

**SynthesisMaterial** allows connections and tensions to be represented without silently converting
connections into facts.

**DoorwayCandidate** allows any mode to propose a useful Archive doorway while retaining final
canonical authority at USE.

**OperationResult** provides explicit success/delegate/retry/unavailable states.

**VisitorLanguageBoundary** prevents internal structures from leaking into visitor-facing prose and
preserves HRN's stronger local behavioral boundary.

## Validation

The current branch contains:
- QA/SHARED_CONTRACT_DRAFT.md
- QA/SHARED_CONTRACT_DRAFT_TEST.py
- QA/SHARED_CONTRACT_PROBES.py
- QA/SHARED_INTELLIGENCE_MATRIX.py
- QA/CROSS_MODE_CAPABILITY_AUDIT.md

No production module imports this substrate, and no protected production asset is changed.

## Next gate

The next meaningful step is not more interface design. It is a **behavioral comparison harness**
against representative USE and HRN cases. That harness should show where the same contract genuinely
serves both systems and where apparent commonality is actually domain-specific.

Promotion requires measured reduction in duplicated logic without degradation of HRN relational
behavior or USE macro behavior.