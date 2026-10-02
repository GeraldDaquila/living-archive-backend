# v487.86 Claim Normalization Seam

The shared claim normalizer is introduced through one bounded USE answer-composition seam.

## Boundary
The shared `normalize_claims` transformation operates only on already-constructed claim material. USE retains candidate generation/ranking, canonical authority, visitor-facing composition, specialist routing, HRN voice/state, and provider selection.

## Compatibility
The legacy claim dictionary remains the outward shape. The shared primitive may normalize text, deduplicate propositions, preserve epistemic treatment, and preserve source linkage. It does not select canonical resources or generate visitor prose.

## Protection
`use_core.py`, `main_v487_28_runtime.py`, specialist adapters, and the HRN contribution contract remain protected.

## Validation
The seam is gated by protected-asset QA and focused compatibility probes before merge.
