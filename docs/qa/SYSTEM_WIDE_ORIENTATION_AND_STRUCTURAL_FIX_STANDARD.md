# Living Archive — System-Wide Orientation and Structural Fix Standard

**Status:** Proposed operational standard for review and adoption
**Scope:** The entire Living Archive navigation ecology: The Guide / USE, Living Glossary, Catalogue, Atlas, Glyph Finder, Human Relational Navigator (HRN), Fractal Systems Diagnostic (FSD), and their handoffs, shared retrieval, presentation, and measurement layers.
**Authority boundary:** This standard governs requirements, diagnosis, testing, and evidence. It does not authorize unreviewed runtime changes, edits to protected `use_core.py`, corpus re-embedding, or production deployment.

## 1. North-star principle

Every interaction should help a visitor move from their own question toward more informed understanding while preserving the distinction between evidence, interpretation, and navigation.

The Archive is a navigation ecology, not one generic search box. Each specialist has a distinct responsibility. The system must select the form of help that fits visitor intent and preserve that intent through retrieval, response composition, handoff, and display.

A polished answer is not sufficient evidence of success. The visitor must receive the right kind of help, and any claim of success must be supported by testable evidence.

## 2. Cross-ecosystem invariants

1. **Intent before destination.** Classify what the visitor is trying to accomplish before choosing a specialist or destination. Keywords and similarity scores may inform the decision but must not alone override explicit intent.
2. **Specialist boundaries remain distinct.** Glossary lookup, Catalogue discovery, Atlas orientation, Glyph finding, relational navigation, systems diagnosis, and general Guide composition must not collapse into one undifferentiated behavior.
3. **Answer before optional navigation.** When the question can responsibly be answered directly, answer it before presenting an optional doorway. Respect explicit requests not to navigate away.
4. **Evidence provenance survives every stage.** Distinguish (a) established general knowledge, (b) direct canonical Archive evidence, (c) related source material, and (d) system-generated interpretation or synthesis. Do not present one category as another.
5. **Source fit beats link count.** Recommendations must be relevant to the visitor's intent and accurately describe what the destination offers. Do not add a doorway when none helps.
6. **Uncertainty is calibrated.** State material limitations plainly; do not refuse established general facts merely because the Archive lacks matching evidence, and do not invent Archive support for an unsourced claim.
7. **Visitor agency is preserved.** Offer useful pathways and alternatives without presuming the visitor's beliefs, needs, or next decision.
8. **Human voice and accessibility are product requirements.** Prefer clear, concrete, humane language; avoid internal jargon, robotic templates, decorative clutter, unreadably small text, and redundant links.
9. **Privacy is part of measurement.** Collect only the event data needed to improve the service, minimize retention, and do not infer sensitive personal attributes from query content.
10. **Protected architecture remains protected.** Honor frozen-file, corpus, embedding, environment, and deployment constraints recorded for the affected subsystem.

## 3. Required structural-fix record

Every cross-system defect fix must record the following fields in its issue, pull request, or linked QA artifact:

1. **Observed failure:** exact visitor prompt, actual output/route, surface, timestamp or run identity, and evidence. Separate observation from hypothesis.
2. **Intended behavior:** visitor-centered acceptance criteria, including prohibited behavior.
3. **Root cause:** confirmed failing decision, contract, dependency, or state transition; label unconfirmed hypotheses explicitly.
4. **Correct layer:** intent classification, routing/arbitration, retrieval, evidence grading, answer composition, specialist handoff, rendering/accessibility, instrumentation, or another named layer.
5. **Invariants and protected boundaries:** files, services, specialist roles, contracts, corpus/embeddings, and deployment limits that must remain unchanged.
6. **Regression matrix:** failing case, neighboring positive cases, deceptive near-neighbors, explicit-intent cases, negative controls, and relevant specialist/handoff interactions.
7. **Evidence of success:** named automated tests, contract/integration tests, live API checks, browser E2E where relevant, and exact commit/runtime/deployment identity. Never conflate a mocked UI test with live browser verification.
8. **Closure status:** verified, partially verified, or unresolved; remaining risk; rollback/containment plan when relevant.
9. **Regression prevention:** reusable test or benchmark, owner/area, and conditions that should trigger retesting.
10. **Deployment statement:** explicitly say whether production changed. A merged documentation/test PR is not a deployment.

No fix is considered structurally verified solely because the original example passes. At least one neighboring case must show that intended behavior remains distinct, and relevant negative controls must show that the fix does not broaden the behavior incorrectly.

## 4. Intent and evidence matrix

Use this as the minimum conceptual routing contract. Actual specialist names may vary by implementation, but the user-facing purpose must remain stable.

| Visitor need | Expected response pattern | Common failure to prevent |
|---|---|---|
| Established general fact | Direct, accurate answer; qualify important conditions; identify general-knowledge basis when provenance is surfaced | Archive-only refusal or irrelevant Glossary handoff |
| Meaning of a term in the Archive | Canonical Glossary definition and useful context | Generic answer that ignores Archive-specific meaning |
| “What does the Archive say?” | Source-grounded answer with canonical work or passage | Unsourced synthesis presented as doctrine |
| Find a book, resource, case, or item | Catalogue/resource discovery with a relevant destination | Broad essay instead of findability |
| Map a concept, domain, or territory | Atlas/map-oriented navigation | Flat keyword results without orientation |
| Find a glyph or symbol | Glyph Finder behavior | Glossary or general Guide diversion without reason |
| Understand a relationship or interaction | HRN-style relational orientation within its non-diagnostic boundary | Prescriptive, therapeutic, or falsely certain conclusions |
| Diagnose a system/fractal pattern | FSD diagnostic navigation within its defined remit | Treating a diagnostic request as ordinary Q&A |
| Explore connections across concepts | Clearly framed synthesis plus evidence and useful next pathways | Unmarked interpretation or false claims of canonical support |
| Explicitly request a destination | Honor the requested destination when valid and safe | Generic conceptual routing overriding explicit intent |
| Ask not to be redirected | Answer in place and suppress immediate handoff | Direct page handoff despite explicit instruction |

## 5. Provenance and response presentation

Where the product UI supports it, make the following distinctions inspectable and understandable:

- **Direct answer:** what the response says.
- **Basis:** general knowledge, direct Archive source, related source, or system interpretation.
- **Source/pathway:** canonical title, document type, relevant passage/concept, and a working link when available.
- **Relationship to the question:** why this source is relevant and what it can help the visitor explore.
- **Limits:** important uncertainty or missing evidence, only when it materially changes how the response should be understood.

Do not force all five elements into every response. A simple factual answer may need only a concise qualification. A source-grounded Archive answer should make its source inspectable. A synthesis should label its interpretive status. Keep answer composition and destination recommendation independently testable.

## 6. Regression and verification requirements

For each structural change, select tests appropriate to the affected layer:

- Unit/contract tests for the specific decision and its invariants.
- Neighboring-intent tests to detect overbroad keyword rules or routing changes.
- Negative controls for known failure modes and inappropriate handoffs.
- Specialist integration tests where routing crosses subsystem boundaries.
- API-level E2E for real service contracts and primary/mirror parity when applicable.
- Real browser E2E for claims about visitor-facing rendering, interaction, or WordPress behavior.
- Accessibility and viewport review for material layout or readability changes.
- Privacy/security review when new telemetry or visitor data collection is introduced.

Every QA report should identify the tested source commit, registry revision, service/runtime identity, test type, result, and any untested boundary. A passing backend test does not prove the WordPress visitor interface works; a mocked UI test does not prove live browser behavior.

## 7. Gold Standards and regression registry

The central Gold Standard Registry is the versioned source of truth for approved response behavior. Each record should preserve, when applicable:

- exact query and approved response;
- intent class and intended specialist/destination;
- provenance/evidence basis and canonical source;
- doorway decision, including an explicit no-doorway expectation where appropriate;
- positive, neighboring, and negative assertions;
- source of approval and evidence boundary;
- rating/approval status, without inventing missing historical evidence;
- freeze policy and the test that enforces it.

Keep approved answer examples separate from negative regression controls, implementation-only responses, reconstructed candidates, and unrecovered records. Never upgrade a case to Gold Standard solely because it passes an automated test. Approval and historical exactness are separate facts.

## 8. Measuring genuine orientation

Traffic and clicks are activity metrics, not proof of orientation. Measure a balanced set of indicators:

1. **Intent fulfillment:** did the visitor receive the kind of help requested?
2. **Evidence engagement:** did the visitor inspect a relevant canonical source or resource?
3. **Perceived orientation:** optional, low-friction feedback asking whether the result clarified where to begin or what to explore next.
4. **Productive continuation:** relevant source visits, useful reformulations, and return journeys; interpret repeat searches as either curiosity or unresolved failure based on context.
5. **Trustworthiness:** source accuracy, provenance integrity, unsupported-claim rate, misrouting, irrelevant handoffs, and refusal errors.
6. **System health:** latency, errors, empty-result rate, recovery rate, primary/mirror parity, and specialist failure rates.

Segment results by broad query-intent class and surface so aggregate click-through cannot conceal a failing specialist. Establish a baseline before setting numerical targets. Do not claim causal improvement from a simple before/after comparison when traffic mix or other changes could explain it.

Telemetry should use data minimization, bounded retention, access controls, and aggregate reporting wherever possible. Do not store full query text by default unless a documented, necessary QA use requires it and appropriate safeguards apply. Do not infer sensitive traits or use visitor behavior to make personal judgments.

## 9. Operating cadence

- **For every fix:** complete the structural-fix record and the relevant regression matrix before declaring closure.
- **For every release:** run the required subsystem contracts, protected-boundary checks, and relevant end-to-end tests; record what was not tested.
- **For recurring failures:** group them by root cause, route, and subsystem rather than patching each prompt independently.
- **For Gold Standards:** add or update approved examples only with traceable approval and provenance; preserve negative controls.
- **For analytics review:** periodically examine query classes, no-result cases, route corrections, source engagement, and visitor feedback to prioritize structural and editorial work.
- **For release/deployment:** use the project's explicit release authority and environment constraints. This document itself does not authorize deployment or modify runtime behavior.

## 10. Adoption checklist

A change is ready for acceptance when reviewers can answer yes to all applicable items:

- [ ] The actual visitor intent is identified, not inferred from one keyword alone.
- [ ] The correct specialist and response type are specified.
- [ ] Evidence type and provenance are not conflated.
- [ ] Answer and destination recommendation are independently evaluated.
- [ ] The root cause and fix layer are supported by evidence.
- [ ] Protected files, specialist boundaries, and corpus/embedding constraints are respected.
- [ ] The original failure, neighboring cases, and negative controls are tested.
- [ ] Test type and live verification claims are accurately labeled.
- [ ] Gold Standard or regression records preserve approval status and provenance.
- [ ] Any telemetry is privacy-conscious and tied to an explicit improvement question.
- [ ] The final status names residual risks and whether production was changed.

## 11. Initial operationalization plan

1. Adopt this document as the common review checklist for new structural-fix PRs across the repository.
2. Link it from the Gold Standard Registry and require relevant registry tests to validate that the standard remains present.
3. Apply the matrix first to high-impact regressions: wrong specialist routing, Archive-only refusal of established facts, unsupported source claims, irrelevant doorways, and answer/handoff contract failures.
4. Audit existing telemetry and Microsoft Clarity instrumentation against the measurement and privacy requirements before adding new collection.
5. Build an intent-class regression suite from approved and candidate cases, preserving approval distinctions.
6. Report coverage and unresolved gaps before claiming the whole ecosystem is compliant.

**Implementation boundary:** This PR should add the standard and its documentation/test wiring only. Runtime changes, new visitor telemetry, and deployment require separate scoped work with their own evidence and review.
