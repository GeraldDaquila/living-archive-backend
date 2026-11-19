# The Guide — Capability Accumulation Programme Charter

**Status:** Governing destination and cross-thread continuity record  
**Established:** 2026-11-19  
**Applies to:** The Guide visitor experience, operational telemetry, Gold Star v2 evaluation, governed learning, and controlled runtime capability application  
**Repository:** `GeraldDaquila/living-archive-backend`  
**Production rule:** This charter does not authorize production changes, deployment, autonomous learning, visitor-content collection, or registry mutation.

## 1. Purpose and source of truth

This document records the destination, dependencies, work packages, acceptance gates, operating constraints, and current checkpoint for moving The Guide toward governed capability accumulation.

It exists so the project does not depend on ChatGPT conversation history, context windows, or a single assistant instance. **The repository is the durable source of truth; conversation memory is not.**

At the beginning of every work session:
1. Read this charter and inspect its latest checkpoint.
2. Read `docs/qa/GOLD_STAR_V2_DESTINATION_AND_CONTINUITY_CHARTER.md` and the governing Gold Star standards it identifies.
3. Inspect the current telemetry implementation/PR from the parallel telemetry work before proposing or repeating changes.
4. Inspect exact branch heads, open PRs, CI results, and deployment state relevant to the task.
5. Reconcile repository evidence with this charter. Repository evidence overrides stale chat summaries.
6. Do not ask the owner to repeat information already available in the repository.

After material work, update this charter with verified implementation state, exact SHAs, tests, blockers, decisions, and next actions. Never report a test, review, merge, or deployment without tool evidence.

## 2. Governing principle

The **Capability Accumulation Principle**, now incorporated into `docs/qa/GOLD_STAR_ADAPTIVE_INTELLIGENCE_STANDARD_V2.md`, governs this programme.

Every proposed change must be evaluated for its ability to improve a reusable architectural capability. Prefer structural corrections over isolated answer patches; preserve exact-query Gold Star authority and reviewed transfer boundaries; test against established benchmarks, negative controls, and unfamiliar questions; promote only evidence-backed improvements.

More questions do not automatically make The Guide more intelligent. They create learning opportunities. Capability accumulates only when evidence is interpreted, a reusable improvement is authorized, and transfer is demonstrated through evaluation.

The target is not autonomous self-modification. It is a continuously improving system whose learning is bounded, reviewable, reversible, privacy-conscious, and accountable.

## 3. Destination lifecycle

1. Observe visitor experience through privacy-minimized behavioral telemetry.
2. Observe engine execution and quality through separately governed diagnostic/evaluation evidence.
3. Identify recurring strengths, limitations, and unmet reasoning demands.
4. Extract candidate reusable reasoning principles from appropriately authorized evidence.
5. Review candidate lessons, their qualifying contexts, and abstention boundaries.
6. Test proposed improvements offline against existing Gold Stars, negative controls, and unfamiliar held-out questions.
7. Apply approved, versioned capability packages in shadow mode before any runtime use.
8. Enable only bounded runtime application after explicit authorization and release gates.
9. Monitor quality, regressions, visitor utility, and correctability; roll back when required.

This is a governed development and release cycle. It does not imply that the live Guide currently learns automatically.

## 4. Two distinct evidence streams

### Stream A — Visitor experience telemetry

Purpose: understand how people use The Guide, which visitor journeys work, where people continue exploring, and where they disengage.

Potential event categories, subject to the approved telemetry implementation:
- Guide page entry and session lifecycle;
- question submission event/count, without storing raw question text in analytics;
- response completion and coarse outcome;
- recommendation/resource impression and click;
- follow-up interaction and session exit;
- return/continuation indicators where privacy and consent rules permit.

The exact event schema, retention, consent, aggregation, and WordPress/frontend integration must be taken from the canonical telemetry implementation and its review—not invented or duplicated here.

### Stream B — Engine capability and quality evidence

Purpose: establish whether The Guide understood and completed the task competently, honestly, and appropriately.

Potential evidence:
- question-family/task classification;
- route and provenance class;
- exact Gold Star match or governed structural guidance selection;
- evidence availability and validation outcome;
- question-contract and response-envelope versions;
- repair, abstention, handoff, or error outcome;
- benchmark/held-out evaluator results and human scorecards.

Do not collect raw visitor question or answer text into general analytics or operational logs merely to make the system appear observable. Any use of visitor content for learning requires a separately reviewed legal, privacy, consent, minimization, access, retention, and deletion policy. Prefer curated calibration questions and authorized, de-identified evidence cohorts.

### Separation and convergence

Behavioral telemetry can inform visitor-journey and product decisions; it cannot certify answer quality. Engine quality evidence can inform reasoning and capability decisions; it does not by itself establish visitor satisfaction or usefulness.

The streams may inform the same governed improvement review, but must not be indiscriminately joined or used to infer intellectual quality from clicks, dwell time, or return visits.

## 5. Work packages and acceptance gates

Work packages use the prefix **CAP-WP** to distinguish this programme from the separate WP0–WP5 sequence in the Gold Star v2 implementation charter. They are ordered by dependency; do not implement them as disconnected patches.

### CAP-WP0 — Telemetry reconciliation and visitor baseline

**Purpose:** Establish the actual state of the parallel Guide telemetry work and produce a verified visitor-experience baseline.

Tasks:
- Inspect its branch, PR, changed files, event schema, frontend controller/WordPress integration, tests, and deployment status.
- Reconcile its design with privacy constraints and this charter.
- Identify exactly what is implemented, tested, deployed, or still proposed.
- Complete telemetry in its existing workstream; do not duplicate it here.
- Document event semantics, consent/retention, aggregation, access, and failure behavior.
- Establish baseline visitor journeys and resource-continuation measures only after event correctness is verified.

**Acceptance:** A versioned event contract; privacy review; tests proving raw question/answer content is not sent to general analytics; verified event delivery and deduplication; documented retention/access; and a reproducible baseline report. A design document or mocked event alone is not completion.

### CAP-WP1 — Engine quality observability

**Purpose:** Connect quality evidence to attributable execution without turning visitor analytics into conversation surveillance.

Tasks:
- Define a privacy-safe correlation mechanism between an evaluation case and its execution evidence.
- Record route/provenance, contract versions, validation/repair/abstention outcomes, and runtime commit identity where appropriate.
- Preserve distinctions between LLM, deterministic, exact-answer, specialist, handoff, and failure paths.
- Ensure telemetry failure cannot disrupt visitor answers.
- Keep operational logs free of raw visitor question/answer content.

**Acceptance:** Tests demonstrate correct attribution for supported paths, privacy invariants, bounded diagnostic payloads, and graceful behavior when telemetry is unavailable. A log line alone does not prove quality.

### CAP-WP2 — Governed learning extraction

**Purpose:** Turn evidence into candidate reusable lessons without granting candidates authority.

Tasks:
- Detect recurring failure patterns and candidate strengths from appropriately authorized, de-identified, reviewed evidence.
- Separate answer content from transferable reasoning discipline.
- Require evidence provenance, unique case identity, minimum diversity, and explicit qualifying contexts.
- Define abstention boundaries and target/adjacent/unrelated negative controls.
- Keep candidate detection separate from lesson authoring, approval, and registry mutation.

**Acceptance:** Candidate dossiers are reproducible and evidence-backed; privacy and consent checks pass; weak, duplicate, unreviewed evidence is rejected; no candidate can write the canonical registry or activate runtime behavior.

### CAP-WP3 — Offline capability accumulation

**Purpose:** Demonstrate that an architectural change improves a defined class of questions, including unfamiliar ones.

Tasks:
- Evaluate the triggering case and relevant question families.
- Re-run approved/frozen Gold Stars and negative controls.
- Use representative held-out questions and unfamiliar challenge cases.
- Compare before/after outcomes with route/provenance attribution.
- Track critical failures, false positives/negatives, abstentions, and regression rates.
- Obtain independent human calibration where semantic judgment is required.

**Acceptance:** Exact candidate commit and evaluation inputs are recorded; no critical regression is hidden by aggregate scores; improvement transfers to held-out questions; existing authority and abstention boundaries remain intact; human review is not represented by automated scoring.

### CAP-WP4 — Controlled runtime application

**Purpose:** Allow explicitly approved structural guidance to influence eligible visitor responses within narrow, reversible boundaries.

Tasks:
- Package approved lessons as versioned, immutable releases.
- Require explicit authority, reasoning family, qualifying context, and abstention boundary.
- Match only eligible question contexts; abstain on ambiguity or weak fit.
- Begin in shadow mode with no visitor-facing effect.
- Compare shadow selections and outcomes against offline evaluation and human review.
- Enable bounded application only after explicit owner authorization and a separate release review.
- Provide kill switch, version pinning, audit trail, and rollback.

**Acceptance:** Shadow evidence shows correct target matches and reliable adjacent/unrelated abstention; no exemplar answer text/facts/examples/citations/doorways leak across questions; runtime can be disabled and rolled back; production activation is separately authorized.

### CAP-WP5 — Continuous governance and capability review

**Purpose:** Make improvement a durable operating discipline.

Tasks:
- Maintain periodic visitor-experience and engine-quality reviews as separate reports.
- Prioritize recurring architectural weaknesses over isolated answer patches.
- Review Gold Star coverage, unfamiliar-question transfer, critical regressions, unsupported claims, appropriate abstention, and corrective-intervention frequency.
- Review visitor continuation only as a product/experience signal, never as a proxy for answer excellence.
- Update standards, tests, release notes, and this charter as decisions change.

**Acceptance:** Each cycle has an auditable evidence dossier, human/owner decisions where required, exact code and lesson versions, tests, release/rollback decisions, and a current repository checkpoint.

## 6. Measures of progress

Track direction and denominators; do not set arbitrary quotas or collapse distinct measures into one score.

| Measure | Intended direction | Interpretation |
|---|---|---|
| Gold Star-quality acceptance by question family and route | Increase | Quality coverage, with denominator shown |
| Success on unfamiliar held-out questions | Increase | Primary evidence of transferable capability |
| Critical semantic failures and regressions | Decrease | Safety and reliability |
| Unsupported claims / provenance defects | Decrease | Epistemic integrity |
| Appropriate abstention on unsupported or unrelated tasks | Improve | Correct capability boundaries |
| Isolated answer-specific patches | Decrease | Less symptom fixing |
| Reusable architectural improvements | Increase | Higher leverage |
| Visitor continuation into relevant resources | Improve where useful | Experience/navigation signal only |

The primary adaptive-capability indicator is improved performance on unfamiliar questions without degrading established behavior. More approved Gold Stars, more interactions, more clicks, or higher dwell time are not by themselves proof of learning.

## 7. Operating constraints and safety invariants

- The Guide is live and heavily visited. Production disruption is unacceptable.
- Primary and USE2-Mirror remain protected production services. Preserve the owner's 70:30 primary/mirror distribution.
- Standalone QA is the designated laboratory. Do not use production services as test environments.
- No production deployment, traffic/configuration change, WordPress change, credential change, or Pinecone mutation without explicit authorization and a verified release plan.
- Do not borrow production credentials for QA. Do not trigger paid provider usage or unnecessary provider/Pinecone traffic.
- Preserve the 384-dimensional local embedding contract; no dimension change or reindex without separate authorization.
- Cowboy MCP remains the sole WordPress admin authority.
- Use feature branches and PRs; no direct `main` edits.
- Do not claim independent human calibration when review was delegated or automated.
- Do not activate autonomous registry writes, runtime lesson mutation, or self-modifying code.
- Keep exact Gold Star authority, benchmark IDs, provenance, freeze rules, transfer permissions, and abstention boundaries intact.
- Telemetry must fail safely and must never become a dependency that blocks a visitor response.
- No raw question/answer text in general analytics or operational logs. Any separately authorized content-based evaluation must have its own privacy and governance controls.
- Do not optimize clicks, dwell time, or repeat visits at the expense of direct, honest, useful answers.

## 8. Relationship to the Gold Star v2 charter

This programme does not replace or silently rewrite `docs/qa/GOLD_STAR_V2_DESTINATION_AND_CONTINUITY_CHARTER.md`.

The Gold Star v2 charter remains authoritative for its question-contract, evidence validation, bounded repair, representative evaluation, governed Gold Star transfer, QA deployment, and release gates. This programme adds the visitor-experience telemetry stream and integrates it with a broader capability-accumulation operating cycle.

Where both programmes touch engine quality, registry governance, runtime transfer, or release safety, the stricter existing Gold Star rule applies. Conflicts must be investigated and explicitly resolved; do not silently reconcile them.

Existing implementation in `gold_star_lessons.py`, `gold_star_pattern_detection.py`, related tests, and Gold Star v2 workflows is an existing foundation—not proof that end-to-end capability accumulation is active or complete.

## 9. Cross-thread handoff protocol

Every substantial work session must finish by updating the checkpoint below and reporting:
- programme work package and task;
- repository, branch, PR, exact head SHA;
- files changed;
- tests run and exact results (including skipped, missing, or failed checks);
- deployment/runtime identity only if deployment occurred;
- decisions and approvals obtained;
- unresolved blockers and risks;
- next concrete action;
- explicit statement that production was or was not touched.

At the next session, inspect GitHub state rather than relying on the previous chat summary.

## 10. Current checkpoint — established 2026-11-19

### Verified programme state

- This charter is a destination and tracking specification, not evidence that its work packages are complete.
- The Capability Accumulation Principle is incorporated into `docs/qa/GOLD_STAR_ADAPTIVE_INTELLIGENCE_STANDARD_V2.md` on `main` through merged PR #1735, merge commit `3e8c04c5f22a6125d7edf280474d305544455765`.
- The Gold Star v2 implementation and continuity state remain governed by `docs/qa/GOLD_STAR_V2_DESTINATION_AND_CONTINUITY_CHARTER.md`. Re-read its latest version before work on those areas; it records WP1/WP2 implementation checkpoints, partial WP3, governed WP4 foundations, and outstanding QA/provider/human/browser acceptance gates.
- The repository contains privacy-related telemetry controls/tests, including `tests/test_primary_telemetry_privacy.py` and `tests/test_gold_star_shadow_telemetry.py`. These do not, by themselves, prove the parallel visitor-page telemetry project is implemented or deployed.
- The parallel visitor telemetry work is a separate in-progress effort referenced by the owner. Its exact branch, PR, event schema, implementation state, and acceptance evidence must be discovered and reconciled before CAP-WP0 is marked complete. Do not infer its status from this charter or create a duplicate implementation.
- No visitor telemetry deployment, runtime learning activation, autonomous lesson approval, registry mutation, or production release is authorized by this charter.

### Initial next actions

1. Inspect the parallel telemetry project's current GitHub branch/PR and exact changed files. Read its implementation and tests; establish what is genuinely complete versus proposed.
2. Reconcile its event contract and privacy model with CAP-WP0. Record exact evidence and any conflicts here.
3. Complete CAP-WP0 in its existing workstream, with Standalone QA/staging validation and a separate controlled release gate.
4. Map current engine diagnostic evidence for CAP-WP1 without collecting raw visitor content.
5. Do not start runtime adaptive activation until offline evaluation, held-out transfer, human review, shadow testing, and explicit release authorization are satisfied.

**Destination principle:** Every visitor interaction may provide evidence about the experience, and every properly governed evaluation may provide evidence about capability. Neither becomes learning until a reusable improvement is authorized, tested for transfer, and safely applied.
