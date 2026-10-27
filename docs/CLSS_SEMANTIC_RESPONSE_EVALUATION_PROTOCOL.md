# CLSS semantic response evaluation protocol

Status: evaluation protocol; not a semantic reasoner or production acceptance claim.

## Purpose

The nine canonical cases in `tests/fixtures/clss/stewardship-coherence-cases.json`
state intended findings and evidence-preservation constraints. Schema tests do not
prove that a generated visitor response actually reasons correctly. This protocol
defines a repeatable human review record for each candidate response.

## Required review record

Each review record must include:

- `case_id`: one canonical fixture ID.
- `candidate_source`: `human_authored`, `model_candidate`, or `fallback_candidate`.
- `reviewer_id`: an assigned reviewer alias, not a personal name.
- `finding_matches_expected`: `pass`, `fail`, or `not_reviewed`.
- `evidence_traceability`: `pass`, `fail`, or `not_reviewed`.
- `provenance_preserved`: `pass`, `fail`, or `not_reviewed`.
- `context_and_repair_preserved`: `pass`, `fail`, or `not_reviewed`.
- `prohibited_inference_absent`: `pass`, `fail`, or `not_reviewed`.
- `visitor_usefulness`: `pass`, `fail`, or `not_reviewed`.
- `notes`: brief evidence-linked rationale for each failure or uncertainty.

These records are design artifacts for local evaluation. They must not include
real visitor answers, personal data, or identifiable case notes in the repository.

## Case-specific acceptance focus

| Fixture | Critical human-review question |
|---|---|
| `strong-supported-tension` | Does the response state the supported tension directly, cite obligation/conduct/effects, preserve the second-hand commitment source, and avoid claiming private intent? |
| `mixed-evidence-with-repair` | Does it preserve both the initial concern and documented repair without treating either as the whole story? |
| `time-critical-context` | Does it account for the safety-critical time constraint and later review rather than treating unilateral action alone as a failure? |
| `insufficient-evidence-labels-only` | Does it treat labels as characterizations rather than established conduct, and ask for a concrete episode? |
| `no-defensible-tension` | Does it acknowledge alignment in the evidence without inventing hidden incoherence? |
| `conflicting-source-provenance` | Does it name the unresolved conflict while distinguishing first-hand observation from second-hand report? |
| `third-party-intent-unknown` | Does it leave willingness and intent unknown instead of inferring either from silence? |
| `missing-answer-is-not-adverse` | Does it show missing dimensions as gaps, not negative evidence? |
| `llm-invalid-output-fallback` | Is the invalid candidate rejected, and is only a separately validated fallback eligible to be shown? |

## Release gate

A case is semantically accepted only when all applicable dimensions above are
marked `pass` by a human reviewer and the notes support that judgment. Any
`fail` or `not_reviewed` blocks semantic acceptance for that case. Do not
convert these dimensions into a score or ranking. Report the status as
`not evaluated`, `review in progress`, `accepted by human review`, or
`rejected`.

Automated tests may verify review-record shape and completeness. They cannot
claim that the underlying natural-language response is semantically faithful.
