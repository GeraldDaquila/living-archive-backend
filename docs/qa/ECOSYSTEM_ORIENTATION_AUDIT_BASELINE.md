# Living Archive — Ecosystem Orientation Audit Baseline

**Status:** Initial repository-level desk audit; not a certification of live visitor behavior.
**Standard:** [System-Wide Orientation and Structural Fix Standard](SYSTEM_WIDE_ORIENTATION_AND_STRUCTURAL_FIX_STANDARD.md)
**Source baseline:** `main` after merge of PR #852 (merge commit `779ec1496a951b44eb6eede7b5b12223fea0d957`).
**Scope:** The Guide / USE, specialist routing and handoffs, Catalogue, Glossary, Atlas/Glyph discovery where represented, HRN, FSD, source/provenance, visitor presentation, QA, and measurement.
**Production boundary:** This document is an audit plan and baseline only. It does not change runtime code, the protected `use_core.py`, Pinecone corpus, embeddings, WordPress, telemetry, or production deployment.

## 1. What this audit can currently establish

The repository contains meaningful, targeted safeguards already. This is not a greenfield system, and the audit should preserve these investments rather than replace them with a generic new router.

- The Guide has separate contracts for general composition, conceptual relationships, practical application, direct attribute evidence, resource discovery, and several routing boundaries.
- Catalogue resource-search routing has tests for explicit material searches, explanatory questions that must remain in the Guide, preservation of the original query, and request-boundary behavior.
- The Guide outcome-evaluation/FSD boundary has tests that distinguish outcome evaluation from systems-pattern diagnosis and prevent topic-only FSD handoffs.
- Hub and specialist pipe contracts validate request identity, specialist identity, payload preservation, and bounded contributions.
- HRN has dedicated routing, source-sync, adapter, relational-boundary, and visitor-experience tests.
- The Gold Standard Registry validates record uniqueness, approval/status distinctions, provenance, and freeze policy; the live-capture workflow requires explicit opt-in.
- The `/api/integration-audit` contract explicitly states that it reports registration and declared routing mode only. It does **not** claim live provider health or end-to-end visitor journey success.

These are repository-level observations from tracked code and test names/contracts. They do not establish that every visitor-facing route works correctly in production today.

## 2. Initial risk register

| Priority | Risk / audit question | Existing evidence | Required next evidence | Closure criterion |
|---|---|---|---|---|
| P0 | A wrong specialist or destination is selected despite a sensible response being possible | Catalogue/Guide boundary tests; outcome-evaluation vs FSD tests; route-specific tests | A cross-intent replay matrix against the actual request boundary and live primary/mirror services | Intended route passes; neighboring intents and negative controls remain distinct; live evidence recorded |
| P0 | The response's evidence basis is unclear or misrepresented | Direct-attribute evidence boundary; conceptual grounding tests; general-knowledge correction benchmark | Check response payload and visitor display for explicit distinction among general knowledge, canonical Archive evidence, related source, and system interpretation | No unsupported claim of Archive provenance; relevant sources are inspectable where a source is required |
| P0 | Backend passes but visitor interface still fails or displays stale content | Guide Woody mocked UI continuity workflow; live dual-service E2E workflow | Real browser submission on the public WordPress Guide for representative cases; confirm loaded asset/version and rendered output | Browser-level interaction and output verified separately from API/mocked tests |
| P1 | Doorway is irrelevant, premature, or overrides an explicit request | Answer-before-handoff and canonical recommendation pairing tests; Catalogue handoff tests | Paired tests for answer-only, explicit destination, no-redirection request, and source-grounded answer | Correct answer/destination separation and no inappropriate handoff |
| P1 | A specialist's voice or remit is lost at the shared boundary | Hub contract and HRN source-sync tests | Representative live round-trip for each enabled specialist; verify voice, boundary, original question, and payload survive | No voice flattening, request identity loss, or cross-specialist leakage |
| P1 | A narrow fix breaks neighboring routes | Numerous local routing contracts | Shared intent-class regression matrix with positive, near-neighbor, and negative controls | Every change runs affected local tests plus shared route regression battery |
| P1 | Gold Standard status is inferred from a single passing run | Registry schema and provenance contract | Audit records for approval evidence, exact response recovery, and status classification | No candidate or reconstructed response mislabeled as approved historical truth |
| P2 | The response is technically correct but hard to read or interact with | Some mocked UI and human-voice contracts | Real viewport checks for readability, redundant links, keyboard/focus, responsive behavior, and screen-reader labels | Visitor-facing review passes at agreed desktop/mobile widths |
| P2 | Analytics optimize clicks rather than actual orientation | Existing external analytics may be available, but this repository review does not certify current configuration | Inventory current event collection and retention before adding anything; define baseline and privacy review | Measurement combines intent fulfillment, source relevance, feedback, trustworthiness, and system health; no unreviewed data collection |

## 3. Audit sequence

### Phase A — Protect known behavior and verify current live baseline
1. Pin the Gold Standard Registry revision and current application/runtime identities.
2. Assemble the approved query battery by intent class: general fact, Archive-specific definition, “what does the Archive say,” resource discovery, explicit destination, no-redirection request, conceptual relationship, relational exploration, outcome evaluation, systems diagnosis, and safety-sensitive requests.
3. Run the same relevant cases against primary and mirror services. Record the exact request, HTTP result, response contract, provenance fields, doorway decision, and latency.
4. For representative cases, submit through the public WordPress visitor interface in a real browser. Capture asset/version identity and rendered result. Do not infer browser success from API success.
5. Re-run known negative controls, including the historical general-knowledge refusal and the Guide-to-Catalogue misrouting cases.

### Phase B — Map specialist boundaries
1. Compare declared capability registry, enabled adapters, native handoffs, and public visitor-facing entry points.
2. For each enabled specialist, document trigger intent, prohibited triggers, request/contribution contract, voice policy, canonical candidate behavior, and safe fallback.
3. Exercise each boundary with an in-scope query, a near-neighbor query, and an explicit contrary-intent query.
4. Flag missing or contradictory contracts; do not activate planned capabilities merely because they appear in a registry.

### Phase C — Inspect source and destination integrity
1. Sample direct Archive claims and verify source title, destination, and passage/content match the claim.
2. Sample general-knowledge answers and verify they are not presented as Archive doctrine.
3. Sample system-generated interpretations and ensure their interpretive status is clear.
4. Check answer-before-doorway ordering, explicit no-redirection requests, no-doorway cases, and duplicate or indistinguishable links.

### Phase D — Visitor experience and measurement
1. Review voice, reading level, mobile and desktop presentation, keyboard use, and result-state continuity.
2. Inventory existing analytics and data retention first. Do not add new query logging as part of this audit by default.
3. Define an initial baseline for intent fulfillment, source relevance, inappropriate handoffs, unsupported claims, no-result/reformulation, latency, and service parity.
4. Use optional visitor feedback and privacy-preserving aggregate events to assess whether results clarify where to begin; treat clicks as a proxy, not proof.

## 4. Required audit record per test case

Each row in the resulting audit artifact should include:

- case ID and registry revision;
- intent class and exact query or privacy-safe test identifier;
- expected specialist/response pattern;
- expected evidence basis and doorway behavior;
- actual result and route;
- test layer: unit/contract, integration, direct API, mocked UI, or real browser E2E;
- primary/mirror service identity and application commit/runtime when applicable;
- pass/fail/blocked and evidence link;
- defect/root-cause status: confirmed, suspected, or unknown;
- regression coverage added or still missing.

Do not place unnecessary personal or sensitive visitor queries in long-lived reports. Prefer approved synthetic test prompts and aggregate analytics.

## 5. Initial implementation priorities

1. **P0 — Build one shared cross-intent regression matrix** from existing approved and confirmed cases; preserve status distinctions and do not rewrite frozen expected responses.
2. **P0 — Make evidence basis and doorway decisions testable as separate outputs** wherever the current response contract supports them; add contracts only after confirming the current schema and compatibility requirements.
3. **P0 — Keep API, mocked UI, and real browser evidence distinct** in QA reports and release decisions.
4. **P1 — Audit specialist boundaries and neighboring intents** using the existing focused contracts; repair root causes rather than accumulating prompt-specific exceptions.
5. **P1 — Review destination fit and source traceability** for the highest-impact visitor journeys.
6. **P2 — Establish a privacy-reviewed orientation measurement baseline** before introducing or expanding telemetry.
7. **P2 — Run a focused accessibility/readability review** on real visitor-facing surfaces and record concrete defects.

## 6. Exit criteria for the initial audit

The audit is complete only when:
- all enabled visitor-facing specialists and native handoffs are enumerated;
- high-impact intent classes have approved positive, near-neighbor, and negative cases;
- primary/mirror service checks are recorded where both are production targets;
- representative real browser journeys are checked separately from API tests;
- evidence and destination integrity have a documented sample review;
- accessibility and telemetry gaps are explicitly recorded;
- every P0 item has evidence-backed closure or a named unresolved blocker;
- no report claims ecosystem-wide compliance solely from a green registration endpoint or a passing local test.

**Current status:** The audit baseline is documented; the full cross-ecosystem execution and live browser review remain outstanding.
