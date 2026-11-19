# Gold Star Adaptive Intelligence Standard v2.0

**Status:** Approved specification; implementation and release gated on verified tests  
**Authority:** User-approved umbrella-standard elevation, 2026-11-18  
**Scope:** The Guide response composition, evaluation, governed learning, and quality assurance  
**Compatibility:** Additive elevation. Existing approved Gold Star records and their evidence remain immutable unless separately authorized.

## 1. Governing objective

Every response should demonstrate question-appropriate intellectual competence, communicate understanding with clarity and integrity, and provide the visitor with a meaningful resolution or appropriate next step. The system should continuously improve its ability to do so without sacrificing subject-specific judgment, epistemic integrity, or the individuality of each question.

The standard evaluates the quality of the response, not conformity to a universal answer template. Its dimensions are universal expectations whose expression must be selected according to the visitor's actual question, domain, intent, complexity, stakes, and requested outcome.

## 1.1 Capability Accumulation Principle

**Governing principle:** Every proposed code change must first be evaluated for its capacity to improve a reusable architectural capability.

The Guide must become more capable through governed learning from real questions and approved evidence—not merely accumulate question-specific patches or memorized answers.

Operational requirements:

1. **Treat questions as capability probes.** New visitor questions, calibration cases, failures, and successful answers provide evidence about the engine's strengths, limits, and unmet reasoning demands. Volume alone does not constitute learning.
2. **Prefer structural learning over answer patching.** When a weakness appears, identify the earliest responsible layer—question understanding, task/domain classification, capability routing, evidence and provenance, composition, validation, or visitor-boundary enforcement. Correct the shared layer when the evidence supports a reusable correction.
3. **Preserve exact-query knowledge without confusing it with general capability.** Gold Star answers remain question-specific authorities unless a separately reviewed reasoning discipline has explicit transfer permission, qualifying context, and abstention boundaries. Never generalize by copying answer text, examples, facts, citations, or doorways.
4. **Require demonstrated transfer.** A proposed architectural improvement must be tested against the triggering case, previously approved/frozen Gold Stars, relevant negative and abstention controls, and unfamiliar held-out questions. A local pass is not proof of broader capability.
5. **Make improvements cumulative and governed.** Promote reusable improvements through version-controlled, reviewable changes with regression evidence. Observation, candidate lesson generation, or a higher Gold Star count does not authorize runtime learning or autonomous registry changes.
6. **Reduce corrective intervention as capability grows.** The intended trajectory is increasing Gold Star-quality coverage and success on unfamiliar questions, with fewer isolated answer patches and fewer regressions. This is an evidence-based direction, not a quota or a claim that every new question must become a Gold Star.
7. **Preserve subject-specific judgment and correctability.** Generalization must not flatten domain differences, erase uncertainty, widen authority, or prevent future correction. When transfer is uncertain, retain exact-query behavior or abstain.

A successful iteration leaves the engine more capable across a defined class of questions—not merely one answer better. The measure of adaptation is improved performance on questions the engine has not been specifically taught to answer, without degrading established behavior.

**Non-claim:** More questions do not automatically make the engine more intelligent. They create opportunities for learning. Capability accumulates only when evidence is interpreted, a reusable improvement is authorized, and transfer is demonstrated through evaluation.

## 2. Eight integrated quality dimensions

### Layer I — Communication excellence

1. **Prose:** Clarity, precision, readability, appropriate tone, economy, and expressive quality. Language must serve understanding; verbosity is not a proxy for quality.
2. **Structure:** Organization, progression, hierarchy, emphasis, and presentation appropriate to the question. No fixed paragraph count or section sequence applies universally.
3. **Coherence:** Logical consistency, connected reasoning, conceptual integrity, and absence of contradiction. Distinctions and conclusions must follow from the answer's premises and evidence.

### Layer II — Intellectual excellence

4. **Question-fit and competence:** Correctly identify what the visitor is asking, classify the relevant domain and task, and apply suitable subject-specific knowledge and reasoning. Do not substitute generic advice, Archive framing, or a familiar benchmark template for the actual task.
5. **Discernment and epistemic integrity:** Distinguish established facts, source-grounded claims, interpretation, inference, uncertainty, and unknowns. Calibrate confidence; disclose material limitations; avoid unsupported certainty; recognize when to abstain, qualify, verify, or ask a focused clarification.

### Layer III — Human utility

6. **Resolution and practical utility:** Deliver the kind of value the question calls for: an explanation, distinction, method, decision framework, practical action, synthesis, or appropriately bounded answer. The response must address the question before optional navigation or follow-up.
7. **Continuity and developmental value:** Where genuinely useful, identify a relevant next step, a meaningful connection to canonical resources, or a path to deeper exploration. Do not manufacture engagement, append irrelevant doorways, or prolong an answer unnecessarily. Respect explicit requests not to provide a handoff.

### Layer IV — Adaptive excellence

8. **Adaptive learning integrity:** Learn from approved evidence under explicit authority and transfer boundaries. Transfer reviewed reasoning discipline only when question-fit and qualifying context support it. Preserve abstention boundaries, exact-query authority, and subject-specific judgment. Detect regressions and improve through tested, reviewable changes without flattening intellectual diversity.

## 3. Question-dependent application

The eight dimensions are not eight mandatory response sections. The composition system must select their appropriate expression based on the question.

Examples:
- A simple factual question should normally receive a direct, concise, calibrated answer.
- A conceptual or philosophical question may require definitions, distinctions, reasoning, and implications.
- A practical question should provide usable actions before optional follow-up.
- A strategic question may require alternatives, trade-offs, consequences, and a reasoned recommendation.
- A technical question requires precision, reproducibility, and verification appropriate to its stakes.
- An uncertain or contested question requires explicit evidence boundaries and calibrated confidence.

No exemplar's surface structure, wording, claims, examples, citations, or doorway may be copied into an unrelated response. A structural pattern is transferable only within its reviewed qualifying context and abstention boundary.

## 4. Relationship to the existing 112 approved Gold Stars

This specification does not amend, invalidate, renumber, rewrite, downgrade, or retroactively reinterpret any existing approved Gold Star.

The canonical registry remains the sole authority:
- `docs/qa/gold_standard_registry.json`
- Stable identity remains `benchmark_id`.
- Existing approval evidence, answer text, provenance, freeze policy, numbering state, and capabilities remain unchanged.
- Existing exact-answer authority remains exact-query bounded.
- Existing qualitative transfer review remains governed by `docs/qa/gold_star_qualitative_transfer_review.json`.
- No new transfer permission is inferred from this umbrella elevation.
- No existing benchmark is automatically granted deterministic-fallback eligibility.
- The authoritative approved inventory remains status-based. The current 112 approved records and 110 active structural contributors must not be conflated.
- Display serials are not adaptive-learning identities or eligibility criteria.

Any future change to an individual benchmark requires its own evidence, review, and explicit approval under the existing constitutional gate.

## 5. Runtime evaluation contract

A conforming implementation must make the eight dimensions operational in the response-composition and quality-evaluation path, not merely document them.

At minimum, the runtime must:
1. Classify question intent/domain/task sufficiently to select question-appropriate quality expectations.
2. Supply applicable quality guidance to the response composer without imposing a fixed template.
3. Preserve exact-answer authority and the current separation between answer composition and destination recommendation.
4. Use approved Gold Star evidence only within its recorded capability, qualifying context, and abstention boundary.
5. Keep continuity/navigation optional, relevant, and subordinate to answering the question.
6. Evaluate or validate the resulting response against the applicable dimensions, with explicit fail/repair behavior for enforceable defects.
7. Fail safely when guidance retrieval or evaluation is unavailable; do not invent quality evidence or silently widen transfer authority.
8. Expose enough non-sensitive diagnostic evidence for tests and audits to establish which standard version and applicable guidance were used. Do not log visitor query text or answer content merely to prove activation.

A call to a selector, a log line, a prompt comment, or the presence of this document alone does not prove that the standard is active or functioning.

## 6. Evaluation and release gates

Tests must establish both positive behavior and negative boundaries.

### Required question classes
- Direct factual / general knowledge
- Conceptual / explanatory
- Practical / how-to
- Strategic / trade-off
- Technical / verification-sensitive
- Uncertain, contested, or insufficiently evidenced
- Explicit no-handoff / no-follow-up requests

### Required assertions
- Question-fit changes the response approach appropriately.
- Prose, structure, and coherence remain strong without a fixed universal format.
- Claims and confidence are calibrated to available evidence.
- Practical questions receive usable actions before optional follow-up.
- Strategic answers make relevant trade-offs and consequences visible.
- Continuation appears only when useful and warranted.
- Explicit no-handoff instructions are respected.
- Exact approved answers remain exact-query bounded.
- Cross-question transfer uses reviewed discipline only and respects qualifying context and abstention boundaries.
- No exemplar-specific answer text, facts, examples, citations, or doorways leak into unrelated questions.
- Missing adaptive guidance does not cause unsafe or misleading behavior.
- Existing registry integrity, approval, numbering, provenance, and 112/110 count invariants remain unchanged.

### Release rule
No production promotion until:
1. Specification and runtime contracts are reviewed together.
2. Targeted unit, contract, regression, and adversarial tests pass.
3. The existing 112 approved records and 110 active contributors reconcile unchanged.
4. Tests demonstrate actual runtime consumption and observable behavior, not merely document/schema presence.
5. Full CI for the change passes.
6. A reviewer audits representative outputs across the required question classes and verifies negative boundaries.
7. The release evidence identifies the exact commit and standard version.

## 7. Measurement boundary

Response quality and ecosystem performance are related but distinct.

- **Response quality** asks whether the answer is fit, competent, coherent, honest, useful, and appropriately bounded.
- **Ecosystem performance** asks whether visitors explore relevant resources, return, and develop sustained engagement.

Do not optimize answer composition to manufacture repeat visits, clicks, or longer sessions. Measure returning visitors, onward resource exploration, and multi-resource engagement at the product/analytics layer. These outcomes are not proof that an individual answer is excellent.

## 8. Change-control rule

This v2.0 specification is additive to the existing Gold Star governance. Runtime implementation must be isolated on a feature branch, tested offline, reviewed in a pull request, and promoted only after the gates above pass. No production deployment is authorized by approval of this specification alone.

**Governing principle:** Every answer should be appropriate to its question, excellent in its execution, honest in its reasoning, useful in its outcome, and capable of contributing to a continuously improving intellectual environment.


## 10. Runtime enforcement boundary

The v2.0 minimum is source-independent. The Guide enforces the v2.0 floor at both visitor JSON exits: the early-return
`_use_send_json` path and the outer `_send_with_final_visitor_boundary` that
captures ordinary FastAPI `/api/query` responses. This covers both early
specialist/recovery returns and the normal provider-composition path. Each exit
invokes `gold_star_response_floor.evaluate_response_floor` before JSON
serialization, so the ordinary LLM route cannot bypass the floor.

The runtime gate is intentionally conservative and machine-verifiable:
- a successful response must contain a non-empty answer and its originating query;
- generic non-answer markers and unsafe HTML/script-shaped content are rejected;
- the answer must remain within the response-size contract;
- the same checks run regardless of response provenance;
- a gate failure is withheld as a controlled 503 rather than returned as a
  successful answer;
- exact approved Gold Star text is never silently rewritten. If it fails the
  same integrity gate, it is withheld and requires governed review.

This runtime gate is a minimum integrity control, not an automated semantic
judge. It does not claim to prove factual accuracy, question-fit, completeness,
discernment, or usefulness. Those dimensions remain governed by the existing
question-specific contracts, benchmark suites, evidence/provenance checks,
and human audit. The eight dimensions are universal evaluation criteria, not
eight mandatory visible sections in every answer. The LLM may reach a higher
ceiling, but no successful response source is exempt from the minimum.

Specialist protocols that intentionally return structured handoffs or explicit
error payloads are not misrepresented as completed explanatory answers. Their
own contracts remain authoritative for the handoff or error; completed visitor
answers are evaluated by the shared floor.
