# FSD Two-Quantum MVP — Acceptance Contract

Status: candidate implementation in progress; not production-enabled.

## Scope

Implement one FSD diagnostic path inside the existing Living Archive backend. Do not create another Render service, provider gateway, retrieval engine, or diagnostic application. Keep the existing WordPress FSD page as the visitor interface and the existing USE backend as the sole analysis runtime.

## Candidate implementation status

- Added a dedicated `fsd_report_composition` operation to the Provider Bank gateway and capability policy, with a bounded 12-second provider call and one independent fallback.
- Added an authenticated `POST /api/fsd/analyze` route to the existing USE FastAPI application. It validates the request, reuses `use_core.fetch_canonical_context` twice, and does not create another service or retriever.
- Added server-side report validation, exact evidence-ID binding, canonical-domain checks, two-quantum citation coverage, and explicit not-assessed labels for unselected scales.
- Provisional numeric quantum signals remain server-internal; the browser receives neither raw quantum scores nor provider/model identity.
- Added request-body limits, authenticated ingress, a conservative global rate gate, no persistence, and bounded failure responses.
- Added an inactive, feature-flagged WordPress proxy plugin that reuses the existing server-only Provider Bank credential provider. PHP syntax validation passed; the plugin is not activated and the route remains disabled by default.
- The published visitor page still uses local three-category scoring and static result cards; it has no backend request. It is not compatible with the two-quantum report contract and must be revised before the proxy is enabled.
- The live USE specialist registry and adapter registry still do not declare FSD; the new endpoint is deliberately a single narrow path rather than a new specialist adapter.
- USE already owns the Pinecone index, 384-dimensional embedding path, canonical-resource validation, and provider selection. FSD reuses these.

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

The ten existing items are mapped deterministically as follows (zero-based indices in code; numbered here for readers):

| Item | Primary quantum | Rationale |
|---|---|---|
| 1. Significant problem recognition | Q001 Correspondence | Tests whether emerging failure becomes visible. |
| 2. Difficult information | Q001 Correspondence | Tests whether uncomfortable evidence can travel. |
| 3. Location of meaningful authority | Q002 Correctability | Tests whether responsibility is matched by authority. |
| 4. Changing an established pattern | Q002 Correctability | Tests whether attempted correction can take hold. |
| 5. What the system rewards | Q002 Correctability | Tests whether incentives sustain or reproduce the difficulty. |
| 6. Decision-makers and consequences | Q001 Correspondence | Tests whether decision-makers encounter the effects of decisions. |
| 7. Learning from experience | Q001 Correspondence | Tests whether experience changes shared understanding and practice. |
| 8. Response to changing conditions | Q002 Correctability | Tests whether the system can adjust its arrangements. |
| 9. Return of recurring difficulty | Q002 Correctability | Tests whether correction reaches underlying conditions. |
| 10. Room for meaningful leverage | Q002 Correctability | Tests whether a point of effective correction can be located. |

The answer options are ordered from stronger functioning (0) to stronger constraint signal (3). The server recomputes quantum summaries from raw option indices; browser-supplied scores are never authoritative. This is a provisional mapping to be reviewed against the locked Two-Quantum definitions before visitor-facing activation. Do not preserve the legacy perception/agency/reproduction dimensions as visitor-facing diagnostic categories.

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
- The backend route requires the existing Provider Bank shared secret. The WordPress proxy and server-side credential availability are still unverified; do not expose the secret in browser code.
- Apply request-size, answer-count, string-length, and visitor/session abuse limits. The current backend global ingress gate is provisional and does not replace visitor-level throttling at the WordPress proxy.
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
