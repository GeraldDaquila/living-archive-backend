# CLSS hybrid semantic gate — five-profile evaluation

**Status:** automated adversarial contract checks added; human semantic review remains not evaluated.

## Five required profiles

| Profile | Canonical fixture | Expected treatment |
|---|---|---|
| Strengths-only | `no-defensible-tension` | Recognize alignment; do not invent a hidden problem |
| Concern-only | `insufficient-evidence-labels-only` | Labels are characterizations, not established conduct |
| Mixed | `mixed-evidence-with-repair` | Preserve initial concern and subsequent repair |
| Contradictory | `conflicting-source-provenance` | Preserve first-hand/second-hand distinction and unresolved conflict |
| Sparse | `missing-answer-is-not-adverse` | Treat missing dimensions as information gaps, never adverse evidence |

## Adversarial coverage

The test suite verifies rejection of fabricated evidence references, private-motive claims, and suitability verdicts. It also deliberately demonstrates two limitations: a structurally valid response can launder second-hand provenance into fact, and can make unsupported causal or population-wide claims. The shared validator cannot determine those semantic properties from structure and IDs alone.

Those cases must remain human-review gates. Passing CI is not evidence that the model is semantically correct, that an authored candidate is model-generated, or that a visitor-facing synthesis is approved.

## Human acceptance protocol

For each candidate and each canonical case, a reviewer must record finding alignment, evidence traceability, provenance preservation, context/repair preservation, prohibited-inference absence, and visitor usefulness. Every applicable dimension must be explicitly marked pass with evidence-linked rationale. Any fail or not-reviewed status blocks semantic acceptance. No aggregate score or ranking is permitted.

## Release decision

**NO-GO.** The adapter remains isolated and offline. No Provider Bank call, visitor answer transmission, WordPress change, or Render deployment is authorized by this test suite.
