# ADR-001: Deterministic-First Guide Architecture

- **Status:** Accepted — 2026-11-24
- **Decision owner:** Project steward
- **Scope:** The Guide's ordinary visitor-response path and its adaptive-quality governance
- **Related issue:** https://github.com/GeraldDaquila/living-archive-backend/issues/1961
- **Decision baseline:** `af1d0386285d2ae2d5b5c48439c9dc6de1cb40a0`

## Context

The Guide has repeatedly encountered external provider failures, including rate limits, timeouts, unavailable candidates, and provider-bank exhaustion. In the 2026-11-24 developmental-capacities production request, the relevant approved Gold Star was retrieved and exposed in the trusted provider prompt, but provider adjudication was not observed. The visitor received a deterministic recovery. The trace correctly did not certify Gold Star application.

Repeated tuning of provider ordering, timeouts, retries, health state, and fallback admission has not yet demonstrated a proportionate, sustained improvement in the visitor-facing reliability of the Guide. The system must not confuse successful orchestration with successful understanding, nor candidate retrieval or prompt exposure with semantic application.

The Guide's primary value is its ability to understand the visitor's question, apply governed institutional knowledge, produce a complete and coherent response, respect epistemic limits, and provide a relevant Living Archive doorway. External model availability is an implementation dependency, not the product's source of authority.

## Decision

Adopt a **deterministic-first, Gold-Star-governed architecture**.

1. **Gold Star Adaptive Engine — governed quality intelligence.** It supplies reviewed reasoning disciplines, qualifying contexts, and abstention boundaries. Its inventory is dynamic. Exact-answer authority, structural transfer authority, and deterministic-fallback eligibility remain distinct permissions.
2. **Deterministic Response Engine — primary bounded composition.** For question classes with explicit, tested contracts, deterministic composition is the default dependable response path. It must preserve question fit, conceptual distinctions, relational reasoning, epistemic boundaries, and doorway continuity. It must abstain or request clarification outside validated scope rather than fabricate coverage.
3. **Shared validation and evidence boundary — final authority.** Every candidate, whether deterministic or generative, is evaluated for completeness, relevance, coherence, safety, grounding, provenance, and satisfaction of the visitor's actual request.
4. **Provider Bank — optional generative enhancement.** The bank may compose for question classes not yet covered deterministically or enrich a deterministic candidate when available. Provider failure must not block a valid bounded response. Provider output remains subject to the same validation boundary.
5. **Honest provenance.** Deterministic response, provider composition, provider-assisted recovery, cache reuse, provider-reported Gold Star selection, evidence-supported application, and demonstrated quality improvement must remain separately represented. A provider-reported evidence span is an assertion, not proof of semantic quality. Deterministic recovery must never receive provider-applied adaptive-transfer credit.

## Provider Bank operating policy

Move routine provider-bank tuning to maintenance-only.

A proposed intervention is admissible only when all of the following are supplied:

- a reproducible production failure or a clearly bounded operational defect;
- a root-cause explanation supported by trace or test evidence;
- a narrow change and falsifiable improvement hypothesis;
- regression coverage for latency, exhaustion, quota behavior, candidate fairness, response integrity, and provenance as applicable;
- a measurable success criterion and a rollback condition.

Do not add retries, candidates, timeout extensions, or routing complexity merely to increase the number of attempts. If two consecutive targeted interventions fail to improve the relevant production measure, stop tuning and conduct an architecture review before further changes.

## Required engineering work

1. Define and test deterministic-first routing for the question classes already supported by bounded composition.
2. Inventory deterministic coverage by question class, including explicit abstention boundaries and measured outcomes.
3. Audit comparative-question instrumentation. The production restructuring question visibly compared four concepts while its trace reported `comparative_subjects=0`; identify the counter's owner, definition, and measurement failure before changing it.
4. Preserve and test provenance across provider success, provider exhaustion, deterministic recovery, cache reuse, and any post-composition repair.
5. Continue held-out Gold Star evaluation in separate stages: retrieval, prompt exposure, provider selection, semantic application, and outcome improvement. Do not collapse these into a single transfer-success flag.
6. Use paired evaluation and blind review where a claim of quality improvement is made. Do not infer improvement from provider self-report alone.

## Consequences

### Benefits

- External provider outages cease to be an architectural single point of failure for supported question classes.
- Institutional intelligence and response integrity become governed by explicit, testable contracts.
- Engineering effort shifts from repeated provider orchestration adjustments toward semantic application, deterministic coverage, and quality measurement.
- Operational claims become more auditable because response provenance and adaptive-learning stages remain distinct.

### Costs and limitations

- Deterministic coverage will be incomplete and must grow deliberately.
- Novel or high-ambiguity questions may still need generative composition, clarification, or a transparent abstention.
- Deterministic responses can become formulaic or stale unless they are evaluated for question fit, canonical-source alignment, and doorway relevance.
- The Provider Bank remains useful and must be maintained, but it is no longer treated as the foundation of Guide reliability.

## Acceptance criteria

This ADR is considered implemented only when:

- deterministic-first routing is covered by automated tests and deployed;
- supported question classes and their abstention boundaries are inventoried;
- provider exhaustion cannot erase or mislabel a valid deterministic response;
- telemetry accurately distinguishes all relevant response provenance states;
- comparative instrumentation is corrected and regression-tested;
- held-out tests demonstrate that Gold Star structural guidance is applied without copying exemplar-specific content;
- any claimed quality improvement is supported by paired, independently reviewed evidence.

**This ADR records an architectural decision, not a claim that implementation or adaptive-transfer certification is complete.**
