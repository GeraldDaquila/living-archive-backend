# FSD Two-Quantum MVP — Acceptance Contract

Status: design baseline; not production-enabled.

## Scope

Implement one FSD diagnostic path inside the existing Living Archive backend. Do not create another Render service, provider gateway, retrieval engine, or diagnostic application. Keep the existing WordPress FSD page as the visitor interface and the existing USE backend as the sole analysis runtime.

## Current-state blockers

- The published FSD page currently performs its questionnaire scoring in browser JavaScript.
- The page has no analysis API call and no durable session persistence.
- The live USE specialist registry does not declare an FSD capability, and the adapter registry does not contain an FSD adapter.
- The provider gateway allowlist and Provider Bank operation policy do not contain an FSD operation.
- USE already owns the Pinecone index, 384-dimensional embedding path, canonical-resource validation, and provider selection. FSD must reuse these rather than create another retrieval or provider path.
- Existing general Guide routing to the FSD page is a doorway only; it is not diagnostic analysis.

## Contract

A single bounded request accepts:
- contract version;
- request/session identifier;
- one diagnostic subject and selected scale;
- the existing questionnaire answers, with strict count, option, and length validation;
- optional visitor context, bounded and explicitly non-sensitive.

The server, not the browser, owns scoring, retrieval, evidence qualification, and report construction. The browser must not submit scores, provider names, model names, URLs, or evidence records as authoritative inputs.

## Two-Quantum model

- Quantum 001 — Correspondence: assess whether the system can perceive and accurately represent relevant conditions and consequences.
- Quantum 002 — Correctability: assess whether the system can respond to what it perceives, revise decisions and arrangements, and prevent recurring failure. Correctability is broader than feedback integrity.

Map the existing questionnaire items into these two quanta only after each question has an explicit rationale and observable answer-to-quantum mapping. Do not preserve the legacy perception/agency/reproduction dimensions as visitor-facing diagnostic categories.

## Fractal scale

Support the same diagnostic contract at:
1. self;
2. relationships;
3. organization/institution;
4. state;
5. civilization.

A report may describe manifestations at other scales only when the visitor's answers or independently retrieved corpus evidence support them. Do not infer that a condition exists at every scale.

## Evidence and report requirements

Every report must distinguish:
- what the visitor reported;
- what the canonical corpus independently supports;
- what is a cautious synthesis;
- what remains unknown or requires further evidence.

Return one recurring systemic condition, manifestations supported at the selected scale and any evidenced adjacent scales, independent canonical evidence with exact title and URL, strengths/enabling conditions, constraints, and practical next steps. If retrieval does not produce adequate independent evidence, say so and do not manufacture citations or systemic conclusions.

Internal reasoning labels, including SEE / MOVE / REPEAT, must never appear in visitor-facing output.

## Security and resilience gates

- No provider credentials or shared secrets in browser code.
- Authenticate the WordPress-to-backend call or implement a reviewed public abuse-control boundary; do not rely on CORS as authentication.
- Apply request-size, answer-count, string-length, per-session and per-origin/IP limits; fail closed when required controls are unavailable.
- Do not persist raw answers by default. If session recovery is introduced, define consent, retention, expiry, deletion, and access boundaries before enabling it.
- Keep logs free of raw answers, sensitive visitor content, credentials, and generated report bodies.
- Provider exhaustion or retrieval failure must return a bounded, honest unavailable/insufficient-evidence response—not a fabricated diagnosis.

## Required QA before any production promotion

1. Schema and malformed-input tests.
2. Exact two-quantum mapping tests, including boundary and contradictory answer cases.
3. Five-scale tests and no unsupported cross-scale inference.
4. Canonical evidence provenance tests: exact title/URL, duplicate removal, and no unsupported citations.
5. Insufficient-evidence and Pinecone-unavailable tests.
6. Provider Bank success, exhaustion, timeout, malformed JSON, and recovery tests.
7. Authorization, origin, payload-size, rate-limit, privacy/log-redaction tests.
8. WordPress page-to-backend end-to-end test, including error rendering and retry.
9. Primary/mirror compatibility and deployment fingerprint checks.
10. Post-deploy smoke test only after all prior gates pass.

## Release boundary

This branch is an isolated candidate. Do not merge to main, change live WordPress content, alter Render environment variables, or deploy until the implementation and all required tests pass review.
