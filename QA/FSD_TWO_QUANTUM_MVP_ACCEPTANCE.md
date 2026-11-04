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

### Canonical instrument-validity gate

The canonical FSD architecture defines the minimum observed evidence chain as: existing understanding → consequential experience → meaningfully reconsidered understanding → consequential influence on subsequent decision or action. Correspondence concerns the transition from experience to understanding; Correctability concerns the transition from changed understanding to action.

The existing ten-item questionnaire asks about general tendencies across a system. It does not require the respondent to identify one consequential episode, establish the prior understanding, describe the experience that challenged it, show whether understanding was reconsidered, and trace any subsequent response. Several items also blend transitions (for example, learning from experience is worded in terms of changes in practice). Therefore the current question-to-quantum assignment is only a provisional retrieval/query-routing heuristic. It is not a validated measurement model and must not be used to claim that a system has demonstrated or lacks either capacity.

Before visitor activation, either redesign the instrument around one bounded consequential episode and the canonical evidence chain, or explicitly reframe the product as a preliminary self-reported orientation exercise. In either case, reports must distinguish respondent claims from independently supported archive evidence, preserve insufficient-evidence outcomes, and avoid psychometric, causal, or system-capacity claims unsupported by the evidence.

## Fractal scale

Support the same diagnostic contract at:
1. self;
2. relationships;
3. community;
4. institution;
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


### Evidence provenance correction — release blocker

The current candidate's retrieval path returns Living Archive canonical sources, and the report contract requires coverage from both quantum retrievals. Those sources can explain the conceptual architecture, but they cannot independently corroborate that a respondent's reported consequential episode occurred or that the selected system changed its understanding or action. The present report contract risks conflating conceptual references with episode evidence. Before visitor activation, separate respondent-reported episode observations from Living Archive conceptual references, remove any implication that archive retrieval validates the respondent's account, and permit an explicit insufficient-evidence result. See `QA/FSD_EPISODE_INSTRUMENT_V1_PROPOSAL.md` for the proposed episode-based instrument and provenance model.


## Episode contract v2 candidate — implementation status

A separate, versioned episode path has now been added on the candidate branch. It does not replace or silently reinterpret the legacy ten-item tendency contract.

- fsd_episode_contract.py validates fsd-episode-v1, one canonical system boundary, the structured episode fields, bounded optional descriptions, cross-field consistency, and rejects browser-supplied scores/diagnoses/provider settings/evidence.
- The deterministic episode interpretation distinguishes reported transitions, insufficient evidence, warranted non-change, evidence/time deferral, unavailable response capacity, and blocked response. It does not produce a numeric capacity score or stable system diagnosis.
- fsd_episode_report_contract.py binds Living Archive references as conceptual_context_only, fixes the respondent-account provenance as unverified, and imposes a one-episode inference boundary. It rejects explicit language that treats Archive sources as corroboration of the reported episode.
- fsd_episode_api.py adds a separate authenticated POST /api/fsd/analyze-episode route on the existing USE application. It uses static conceptual retrieval queries, optional Archive context, no additional service/retriever, and the existing Provider Bank operation.
- The episode API does not send optional free-text descriptions to the provider; only bounded structured selections are included in report composition.
- The episode route is registered by guide_runtime.py but is not deployed to production. It has not been connected to the WordPress proxy or visitor page.
- The previous /api/fsd/analyze endpoint remains the legacy candidate contract and must not be exposed as the episode instrument.

### New candidate tests

The FSD workflow now includes the episode request contract, episode report provenance contract, and episode API tests. The first episode-contract run exposed a justified-non-change interpretation error; this was corrected. A later report-provenance test exposed a test assertion mismatch; the assertion was corrected. The latest observed successful run before the newest consistency-guard commits reported 86 passed. New regression runs are required for the current head.

### Remaining release blockers

1. Complete the current-head CI and all cross-workflow regressions.
2. Review the episode question wording and interpretation matrix against the canonical FSD architecture; the code is a candidate implementation, not a validated instrument.
3. Confirm the provider processing/retention disclosure before any live submission.
4. Update the inactive browser asset to the episode schema and add safe, conditional question flow.
5. Update the proxy to route only the episode contract to /api/fsd/analyze-episode; keep the old page, plugin, and feature flag inactive until the new UI and backend pass.
6. Add synthetic WordPress proxy → primary → mirror E2E and prove request/response privacy, error handling, retry behavior, and deployment fingerprint.
7. Review and approve before merge or deployment.

The production release boundary remains unchanged: no live WordPress content, proxy activation, feature flag, Render environment variable, or production deployment is authorized by this candidate work.


### Current candidate-head verification — 2026-11-04

At candidate head a79a2c5de5b2e2496d58879b00ae8a0b00a03abc, the FSD contract workflow completed successfully with 89 passed and 1 warning. All nine distinct cross-workflow checks completed successfully: FSD Two-Quantum Contract, v487 production validation, Provider health regression, Provider Bank gateway secret rotation regression, Guide Provider Diagnostics and Pathway Attribution, Guide Provider Health Latency Budget, General Guide provider-bank regression, Guide Woody Mocked UI Continuity Contract, and General Guide Composition Validation. These are CI/automated checks only; they do not replace live WordPress proxy → primary → mirror E2E, UI review, privacy disclosure, or release approval.


## WordPress proxy candidate alignment — 2026-11-04

The installed but inactive Living Archive — FSD Proxy plugin was updated in place to version 0.2.0. Its server-side validator now accepts only fsd-episode-v1, the canonical five scales, the structured episode enums, bounded optional descriptions, and the same cross-field consistency rules as the backend. Its upstream targets now call /api/fsd/analyze-episode on the existing primary and mirror services. The proxy validates the response provenance envelope before returning it, preserves same-origin checks, request-size limits, rate limits, TLS verification, no redirects, bounded response size, no-store headers, and the existing server-only Provider Bank secret helper.

The inactive browser asset was replaced with the episode-based questionnaire and report renderer; it uses no browser storage or analytics, avoids contradictory option combinations where possible, labels the respondent account as unverified, and labels Archive links as conceptual references only. A small responsive CSS asset was added. JavaScript syntax validation passed; the PHP write was syntax-checked by Cowboy MCP. Plugin remains inactive, feature flag remains untouched, and published page 76640 remains unchanged; it does not yet contain the required [data-fsd-app="episode"] mount point. Therefore the proxy route is still not registered and the browser asset is not enqueued. No live WordPress → backend request has been made.


### Additional interpretation and report-grounding corrections — 2026-11-04

A second audit identified two further safeguards and they are now implemented on the candidate branch:

- If the prior understanding is selected as unknown, Correspondence is classified as insufficient evidence. A consequential experience cannot be evaluated as a relationship to an unidentified prior understanding.
- Report composition now explicitly forbids inventing strengths or enabling conditions from the mere presence of feedback, documentation, or action. If the structured answers do not directly support a strength or enabling condition, the provider must return an empty list. Suggested next steps must be framed as suggestions, not asserted events or outcomes.

The browser privacy notice now accurately states that optional short descriptions are sent to the USE backend but are not passed into AI report composition; only structured selections are sent to the configured provider. The report headings were also tightened to distinguish explicitly supported strengths from reported enabling conditions.

Latest FSD workflow at code head 00f244fd8c81479fe35a7a040a5dfe85f28f5d3b: **91 passed, 1 warning**. All nine ecosystem regression workflows passed on the subsequent documentation head 8eaa5a0abb1f94739df4e9265c71f93e2a3ff9a3. The warning is the existing Starlette TestClient/httpx deprecation notice; no test failures were recorded.

WordPress proxy verification after the latest asset update: plugin v0.2.0 remains inactive; PHP source is accepted by Cowboy's PHP syntax gate; browser JS parses successfully; same-origin validation, server-only secret helper, episode endpoint target, accurate privacy notice, and absence of browser storage are confirmed. The published page 76640 is still unchanged and has no episode mount point. No live request or deployment has been performed.


### WordPress asset cache-busting and privacy notice — 2026-11-04

The WordPress proxy plugin version was advanced to v0.2.1 after the final browser-asset copy edits. Both enqueued CSS and JS assets now use the v0.2.1 cache key, preventing browsers from reusing the earlier v0.2.0 assets after activation. Cowboy's PHP write-time syntax gate passed; the final JS asset parses successfully. The proxy remains inactive and the published FSD application page remains unchanged.

The UI privacy notice now states the actual data path: selections and optional short descriptions are sent to the USE backend; only structured selections are included in AI report composition; optional descriptions are not passed to the configured AI provider. Provider-side processing/retention terms may apply to the structured selections. No browser storage or analytics was added.


### Render staging inventory — 2026-11-04

Render inventory confirms the production primary and mirror both track main, with preview deployments disabled. Two historical QA services exist in the primary workspace, but both are suspended and attached to stale branches: living-archive-v340-qa tracks v340-surgical-rebuild (last deployment commit 5b3b0713efc774263749506eaa879352040af00b, 2026-09-12), and living-archive-v334-lean-control tracks v334-release-control (last deployment commit cea718358e5fa2719cb9b7fbff8845f3f27e467e, 2026-09-11). Neither is a current-code staging target. No service configuration was changed. These historical QA services should not be resumed or repointed without a separate controlled review of their environment variables, dependencies, runtime branch, and rollback path.
