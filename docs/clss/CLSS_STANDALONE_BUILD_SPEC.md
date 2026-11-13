# CLSS Guided Reflection — Standalone Build Specification

**Status:** Initial build contract for independent implementation and evaluation  
**Owner:** Living Archive / Coherent Leadership Selection System  
**Integration target:** Later registration as a bounded specialist in USE / The Guide  
**Change boundary:** This document only. Do not modify or deploy production services from this branch.

## 1. Purpose and governing principle

CLSS Guided Reflection is a leadership-preparedness inquiry based on **coherence**, not a conventional leadership profile, personality test, morality test, or ranking instrument. It helps an assessor examine the alignment or divergence among intention, decisions, behavior, relational/systemic effects, recognition/correction, and bounded stewardship.

The tool must help the assessor see what the available evidence may mean and what deserves further inquiry. It must not pronounce someone good/bad, declare a person suitable/unsuitable, infer character from sparse answers, or generate a leadership score.

Build CLSS independently around its narrow and deep task. Do not make the initial build depend on The Guide's routing, request handling, frontend, retrieval orchestration, or protected core. Integration is a later phase through a versioned adapter.

## 2. Product boundaries

### In scope

- A preliminary perspective choice:
  - **My own leadership preparedness**
  - **Another person's leadership preparedness**
- The existing nine open-ended reflection areas, preserved until their current authoritative wording has been checked and explicitly approved for revision.
- Evidence-aware interpretation of the assessor's answers.
- A useful, restrained synthesis that distinguishes supported coherence, possible incoherence, and unresolved unknowns.
- A single justified next step and, only when evidence supports it, one canonical CLSS doorway.
- Deterministic evidence integrity, output validation, safety boundaries, and test fixtures.
- Session-only processing by default.

### Out of scope for the standalone phase

- USE routing or specialist registry changes.
- Changes to `use_core.py` or the Guide's visitor-answer composition.
- Production Render configuration, environment variables, deployments, or provider changes.
- WordPress publication or edits to the existing CLSS draft/plugin.
- Candidate ranking, weighted scores, readiness scores, psychometrics, automated appointment decisions, or claims of validated predictive validity.
- Persisting reflection answers, creating participant profiles, or sending answers to third parties.
- A forced catalogue of predetermined failure modes or a Likert-scale survey.

## 3. Coherence lens

Interpret answers against these connected dimensions without scoring them:

1. **Intention and responsibility** — what the person intends to serve, accepts responsibility for, or may be avoiding.
2. **Decisions and actions** — what was actually chosen or done, under what constraints, and what alternative was available.
3. **Relational and systemic effects** — consequences for people, trust, fairness, feedback, institutions, and systems.
4. **Recognition and correction** — whether tensions or harm are recognized, whether new evidence can change a view, and whether repair is possible.
5. **Bounded and sustainable stewardship** — whether responsibility, authority, limits, continuity, and review are appropriate and sustainable.

The output should help reveal coherence or possible incoherence among dimensions; it must not imply that coherence means conformity to prevailing social expectations.

## 4. Perspective-aware interpretation

The two perspective paths share the same underlying evidence model but must handle epistemic access differently.

### Self-reflection

The assessor can describe their own intentions, experience, actions, and learning. The tool may help them examine mismatches between intention and action, ask what they might be missing, and identify a self-correction or experiment.

Do not assume the assessor's account is complete or perfectly accurate. Preserve their own wording and invite correction when a proposed interpretation may not fit.

### Third-party reflection

The assessor can report observed behavior, statements, documents, effects, and their own interpretation. The tool must distinguish these categories and must not assert that the assessor knows the person's inner motives, private understanding, or unexpressed intentions.

When evidence is limited, the appropriate next step may be to gather corroborating examples, ask a fair question, hear the person's account, or inspect the system/relationship rather than reach a conclusion about the person.

## 5. Evidence and epistemic contract

Every material interpretive claim must be traceable to one or more answer identifiers. Preserve the difference between:

- **Observed** — directly witnessed or documented behavior/event.
- **Reported** — what the assessor or another source says happened.
- **Inference** — a reasoned implication that goes beyond the literal answer.
- **Unknown** — not established by the available answers.
- **Contradicted / tension** — evidence or accounts that pull in different directions and require reconciliation.

Use the shared USE epistemic concepts as candidate vocabulary only; CLSS may define a specialist-owned schema if that prevents loss of meaning. Map into the common specialist contract later.

Non-negotiable handling:

- A blank answer is an **evidence gap**, never negative evidence.
- A single anecdote does not establish a stable trait.
- An allegation is not a verified finding.
- Intent, action, and impact are separate.
- Impact can be real even when intent is unclear.
- Conflicting accounts remain visibly conflicting until resolved.
- An interpretation may offer competing explanations when multiple plausible accounts fit.
- If an inference has no supporting answer reference, reject it or rewrite it as an open question.
- Do not invent corroboration, outcomes, evidence sources, or canonical relationships.

## 6. Interpretation engine

Use a hybrid architecture:

**LLM responsibility:** interpret the particular answers in humane, concrete language; identify possible alignment/tensions; propose alternative readings; state what cannot be concluded; suggest the next useful inquiry.

**Deterministic responsibility:** normalize and validate the answer packet, enforce the output schema, verify answer references, reject unsupported or structurally invalid claims, preserve unknowns and contradictions, validate canonical URLs against an approved registry, and control whether a doorway can be offered.

The LLM must not control its own permission to make a verdict or invent a doorway. Deterministic rules must not precompute a canned interpretation from fixed combinations of answers. If the model is unavailable, the fallback should return a transparent, evidence-organizing summary or request for further evidence—not a fabricated interpretation.

Structured JSON output is a transport contract, not proof of semantic correctness. Semantic correctness must be tested separately.

## 7. Proposed internal output envelope

The exact schema is to be frozen before implementation. The initial contract should express these concepts:

```json
{
  "contract_version": "clss-reflection-v1",
  "perspective": "self | third_party",
  "evidence_map": [
    {
      "claim_id": "claim-1",
      "answer_refs": ["answer-2"],
      "evidence_kind": "observed | reported | inference | unknown | tension",
      "coherence_dimension": "intention_responsibility | decisions_actions | relational_systemic_effects | recognition_correction | bounded_stewardship",
      "statement": "Plain-language interpretation grounded in the referenced answers",
      "alternative_readings": [],
      "uncertainty": "What remains unestablished"
    }
  ],
  "supported_coherence": [],
  "possible_incoherence": [],
  "unresolved_questions": [],
  "next_step": {
    "action": "One concrete, proportionate inquiry or action",
    "rationale": "Why this step follows from the evidence",
    "evidence_refs": []
  },
  "doorway": {
    "status": "recommended | insufficient_evidence | not_needed",
    "stage_id": null,
    "title": null,
    "url": null,
    "rationale": null
  },
  "boundary_notes": []
}
```

This is a conceptual draft, not an already implemented or approved runtime schema. The schema must prohibit unregistered doorway URLs, invalid perspective values, invalid evidence kinds, dangling answer references, and a recommended doorway without a valid canonical registry match.

## 8. Canonical CLSS doorway registry

The only approved stage destinations for this instrument are:

| Stage ID | Canonical stage | URL |
|---|---|---|
| `eligibility_filter` | Eligibility Filter | https://geralddaquila.com/leadership-selection-framework-eligibility-filter/ |
| `stewardship_evidence` | Stewardship Evidence | https://geralddaquila.com/leadership-selection-framework-stewardship-evidence/ |
| `simulation_testing` | Simulation Testing | https://geralddaquila.com/leadership-selection-framework-simulation-testing/ |
| `relational_feedback` | Relational Feedback | https://geralddaquila.com/leadership-selection-framework-relational-feedback/ |
| `reluctance_filter` | Reluctance Filter | https://geralddaquila.com/leadership-selection-framework-reluctance-filter/ |
| `consent_appointment` | Consent Appointment | https://geralddaquila.com/leadership-selection-framework-consent-appointment/ |
| `time_bound_stewardship` | Time-Bound Stewardship | https://geralddaquila.com/leadership-selection-framework-time-bound-stewardship/ |

Framework overview: https://geralddaquila.com/leadership-selection-framework/  
Case studies: https://geralddaquila.com/leadership-case-studies/

The doorway should respond to the most consequential *supported uncertainty or next inquiry*, not simply point to the stage with the most keywords. Return one primary doorway. A second doorway is permitted only if it is genuinely complementary and improves the visitor's next action. If evidence does not justify a destination, return `insufficient_evidence` and explain what would establish fit.

## 9. Deterministic validation and privacy

Before interpretation:

1. Validate the perspective selection and exact answer packet shape.
2. Assign stable answer IDs; do not infer meaning from missing values.
3. Bound input lengths and reject malformed payloads.
4. Keep answers in request/session memory unless later consent and retention requirements explicitly authorize another design.
5. Avoid putting raw reflection answers, names, or sensitive interpersonal details into application logs.
6. Generate a request correlation ID that contains no personal information.

After interpretation:

1. Validate against the approved output schema.
2. Reject references to absent answer IDs.
3. Require evidence references for interpretive claims and recommendations.
4. Ensure `unknown` stays unknown and contradictory evidence is not silently discarded.
5. Ensure third-party interpretations do not claim access to internal motive or intent without a cited direct statement, and even then distinguish a statement of intent from an established fact.
6. Validate the selected doorway against the canonical registry.
7. Fail closed to a useful uncertainty/evidence-gap response if required validation fails.

## 10. Gold Standard evaluation contract

CLSS needs scenario-based evaluation, not just exact-response snapshots. Each scenario should have:
- input perspective and answers;
- source/answer IDs;
- evidence facts that are supported;
- facts or motives that remain unknown;
- prohibited inferences;
- acceptable competing interpretations;
- expected doorway or expected no-doorway behavior;
- a reviewer rubric and provenance.

Required scenario families:

1. Clear self-reflection with good evidence of correction.
2. Self-report where stated intent and observed action diverge.
3. Third-party assessment based on one anecdote.
4. Third-party account containing an unsupported claim about motive.
5. Sparse answers with many blanks.
6. Internally contradictory answers.
7. Two people reporting conflicting versions of an event.
8. Harmful impact alongside benevolent stated intent.
9. Apparent coherence that depends on an untested assumption.
10. Evidence of retaliation, suppressed dissent, or authority without accountability.
11. Evidence suggesting a system design—not just an individual's behavior—may be the source of incoherence.
12. A case where the next responsible step is conversation or corroboration rather than a CLSS-stage recommendation.
13. An input designed to induce moral judgment or social-norm conformity.
14. Provider exhaustion, timeout, invalid JSON, dangling evidence references, and invalid doorway attempts.
15. Self and third-party variants of substantially similar facts to confirm perspective-specific epistemic behavior without changing core evidence standards.

### Acceptance gates

- No numeric suitability/character score.
- Every material inference is traceable to the submitted answers.
- No blank answer treated as adverse evidence.
- No motive or character claims from third-party perspective without adequate cited evidence.
- Contradictions and uncertainty are preserved.
- At least one alternative explanation is presented when the evidence genuinely underdetermines interpretation.
- A doorway is never fabricated, and an unjustified doorway is not forced.
- The output identifies a practical next step proportional to the evidence.
- Provider failure never produces a false verdict or canned adverse assessment.
- The same core behavioral contract holds across supported models.
- The frozen USE/Guide behavior remains untouched during standalone work.

The test results must distinguish unit/contract tests from real model-backed evaluation and browser end-to-end tests. Never report a stage as accepted based solely on prompt review or valid JSON.

## 11. Later USE integration contract

Do not integrate during the standalone build. Once CLSS passes its own gates, implement a dedicated specialist adapter at the existing bounded seam.

Candidate reuse targets identified by source survey:

- `specialist_registry.py`: shared capability contract, after a later explicit integration decision.
- `specialist_adapters.py`: versioned adapter boundary. It returns a bounded contribution; it does not own final visitor-facing prose or canonical authority.
- `shared_intelligence_primitives.py`: candidate evidence, claim, epistemic and doorway structures; validate against their tests and semantics before use.
- `provider_bank.py`: candidate shared model access, capability policy, quotas, timeouts and fallback. Add a CLSS operation only after operation-specific budgets and schema behavior have been tested.
- `general_guide_gold_standards.py` and `docs/qa/gold_standard_registry.json`: learn from approval/provenance controls, but do not force nuanced CLSS interpretation into exact-question/exact-answer standards.
- Existing canonical retrieval may later resolve CLSS source passages, but CLSS conclusions must not be grounded solely in an available destination title.

The current specialist contribution envelope expects versioned identity and bounded fields such as interpretation, perspectives, movement, canonical candidates, boundary notes, safety flags, and specialist-owned payload. Map the CLSS-native contract explicitly; do not weaken the common pipe validator.

Integration invariants:

- USE's router invokes CLSS only when the user requests leadership-preparedness reflection or CLSS is otherwise explicitly selected.
- CLSS remains the owner of coherence reasoning; USE remains the owner of routing and final ecosystem navigation.
- The Guide's general-purpose composition and `use_core.py` remain unchanged.
- Provider selection remains Provider Bank-owned; CLSS must not hard-code a provider key or bypass operation policy.
- No visitor answer is automatically written to persistent storage.
- A single correlation ID joins logs across boundaries without including raw reflection content.
- Failure of CLSS must not degrade search, Catalogue, HRN, or other specialists.
- Specialist registration is not production activation; runtime adapter availability and tests must independently confirm activation.

## 12. Build sequence

1. Confirm the current approved nine question texts and freeze them as the first input contract.
2. Freeze the perspective vocabulary and answer packet schema.
3. Implement the standalone validator and canonical doorway registry.
4. Define and approve the output schema, including failure/insufficient-evidence states.
5. Build synthetic evaluation fixtures with explicit evidence boundaries and adjudication criteria.
6. Implement the model-backed interpreter through an adapter interface that can be mocked in tests.
7. Test malformed answers, provider timeouts, quotas, invalid JSON, unsupported claims and no-doorway cases.
8. Run scenario-based model evaluations, inspect failures, refine shared composition standards and repeat.
9. Conduct human review against coherence principles and the non-verdict boundary.
10. Freeze a CLSS release candidate with source hashes, environment/config identity, tests and evaluation report.
11. Only after explicit integration readiness, map CLSS into USE's specialist contract on a separate integration change and evaluate it against the current frozen ecosystem baseline.
12. Release only after exact-version integration E2E, primary/mirror parity, Catalogue handoff, HRN isolation and browser checks pass.

## 13. Current system limits to respect

The October 27 read-only ecosystem audit recorded:

- Primary service logs show v489.304; mirror logs show v489.297, so primary/mirror runtime parity is not currently demonstrated.
- Render event history reports failed newer builds due to `pipeline_minutes_exhausted`. Do not trigger new deployments while allocation remains exhausted.
- Provider logs include free-tier quota exclusions, rate limits, timeouts, and provider-health-store calls exceeding the configured latency target. Shared Provider Bank reuse must retain per-operation capability and resilience controls.
- The actual production Catalogue and the separate stewardship candidate are distinct Render services. Do not confuse their roles.
- The WordPress Site Health checks returned 9 good, 0 recommended and 0 critical; this is not proof of browser-level acceptance.
- Cowboy MCP is the sole WordPress administration authority. Do not use WPVibe or another WordPress admin path.
- No changes to production WordPress, Render environments, USE routing, or deployments are authorized by this specification.

## 14. Definition of done for standalone CLSS

The standalone instrument is complete only when it produces a useful, humane, evidence-faithful, non-scoring interpretation; handles self and third-party perspectives correctly; never converts missing evidence into a negative judgment; selects an evidence-justified next step or states why it cannot yet do so; passes the scenario suite and model-backed adversarial evaluation; has no unverified provider dependency; and can be wrapped behind the existing USE specialist boundary without changing its reasoning logic.
