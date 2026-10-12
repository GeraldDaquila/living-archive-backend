# Shared Contract Draft — v487.80

## Purpose

Define a minimal common vocabulary for USE and specialist modes without creating a universal
conversation manager or weakening specialist autonomy.

## Contract 1: Evidence Item

EvidenceItem contains:
- id
- title
- url
- text
- provenance

Evidence is source material, not visitor-facing synthesis.

## Contract 2: Claim

Claim contains:
- text
- evidence_ids
- claim_type: definition | relationship | observation | interpretation | exploration
- confidence

Independent source propositions remain distinguishable.

## Contract 3: Inquiry / Movement

InquiryMovement contains:
- surface_input
- orthogonal dimensions
- human_situation (optional)
- desired_movement (optional)
- uncertainty (optional)
- processing_need (optional)
- stage (optional and mode-owned)

USE can supply macro intent. HRN can supply conversational movement. Neither is forced into the
other mode's semantics.

## Contract 4: Epistemic Classification

EpistemicTag:
- supported
- inferred
- interpretive
- visitor-originated
- uncertain

The tag governs treatment; it is not itself visitor-facing language.

## Contract 5: Synthesis Material

SynthesisMaterial contains:
- claims
- relationship_statement
- unresolved_tensions
- perspective_options
- source_ids

Synthesis may connect claims but must not silently turn relationships into facts.

## Contract 6: Doorway Candidate

DoorwayCandidate contains:
- title
- url
- relevance_basis
- source_ids
- candidate_rank

Modes may propose. USE retains final canonical authority.

## Contract 7: Operation Result

OperationResult:
- status: READY | DELEGATE | NEEDS_RETRY | UNAVAILABLE
- mode
- payload
- reason
- contract_version

Failure is explicit. No local generic prose is manufactured solely because an operation failed.

## Contract 8: Visitor Language Boundary

Internal objects remain internal. Visitor-facing language is emitted only after the active mode has
completed a valid composition and its relevant behavioral boundary has accepted it.

HRN's current visitor-response policy remains authoritative for HRN. The common boundary must not
weaken that policy.

## Standardization gate

Promote a contract platform-wide only when:
- at least two modes need the same transformation;
- semantics remain domain-neutral;
- duplication is reduced;
- mode-specific state remains outside the shared contract;
- independent tests can validate it;
- visitor-facing simplicity improves.

This is a contract draft, not production implementation.
