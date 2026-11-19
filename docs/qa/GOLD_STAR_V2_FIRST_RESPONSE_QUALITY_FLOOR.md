# Gold Star v2 — First-Response Quality Floor
**Document type:** Engineering implementation charter  
**Status:** Active implementation target; not a production release authorization  
**Authority:** User direction, 2026-11-19  
**Applies to:** The Guide / USE, every completed visitor-facing answer, every answer-generation source

## 1. Governing objective

Gold Star quality is the default quality floor, not a post-generation repair project. The system should understand the visitor's actual question, select the right kind of reasoning, compose an answer fit for that task, verify it against the available evidence and applicable constraints, and resolve it before delivery.

The target is a reliable, repeatable, robust first response across LLM-generated, exact-reference, deterministic/recovery, and specialist routes. This is a measurable engineering objective, not a claim that any model can guarantee perfection on every possible query. When the system cannot responsibly meet the requested standard, it must expose the limitation, ask one necessary clarification, or abstain rather than disguise a weak answer as complete.

The existing eight-dimension Gold Star Adaptive Intelligence Standard v2.0 remains authoritative. Its dimensions are question-dependent quality criteria, not a fixed response template.

## 2. Two mandatory correction levels

### Level A — Site-wide architecture and engineering

Every completed visitor answer must pass through the same source-independent quality lifecycle, regardless of which model, deterministic function, specialist, or recovery route produced it:

1. **Understand:** identify primary and secondary tasks, domain, stakes, requested outcome, audience, explicit constraints, and ambiguity.
2. **Plan:** select the reasoning operations, evidence standard, response shape, and completion criteria appropriate to that question.
3. **Ground:** identify which claims require canonical Archive sources, external evidence, calculation, code execution, user-provided material, or no additional retrieval. Preserve provenance and distinguish source evidence from inference.
4. **Compose:** produce the requested answer in the right form, using the eight Gold Star dimensions as adaptive criteria rather than mandatory sections.
5. **Validate:** check task completion, factual/evidential support, internal consistency, safety, constraint adherence, useful resolution, and navigation integrity.
6. **Repair or resolve:** allow a bounded, evidence-directed repair for fixable non-frozen answers. Never rewrite frozen exact Gold Stars. If a reliable repair is unavailable, ask a focused clarification or return an honest, bounded limitation.
7. **Deliver:** answer first; add a canonical doorway only when relevant, verified, useful, and not prohibited. Keep the answer and navigation as separate structured fields.
8. **Learn under governance:** use approved exemplars only within their recorded qualifying context and abstention boundary. Transfer reviewed reasoning discipline, never unrelated answer text, facts, examples, citations, or doorways.

The lifecycle must be enforced at shared response boundaries as well as supported upstream by the composer. A final boundary alone cannot manufacture intellectual quality; a prompt alone cannot enforce it.

### Level B — Question-specific intellectual adequacy

Each query must receive a task-appropriate contract. The system must not force every question into a single classifier label or answer shape. It must support multi-intent questions, nested requests, domain-specific standards, different stakes, explicit no-handoff constraints, and unknown or ambiguous tasks.

The question contract must capture, where applicable:

- primary task and secondary tasks;
- domain/subdomain and audience;
- stakes and consequence of error;
- requested output or decision;
- explicit constraints and prohibited actions;
- factual, interpretive, procedural, comparative, strategic, creative, diagnostic, or technical reasoning mode;
- required evidence and provenance standard;
- material uncertainties and unresolved assumptions;
- appropriate response shape and completion criteria;
- whether a clarification, abstention, or canonical continuation is warranted.

Classification confidence must be calibrated. Regex or phrase matching may detect hard constraints and provide routing hints; it must not claim high semantic confidence from a single surface phrase. Unknown and mixed-intent questions must remain valid states, not be forced into a misleading class.

## 3. Current baseline and verified deficiencies

The merged implementation already provides:
- the eight-dimension v2.0 quality contract in the LLM composition prompt;
- the source-independent v2.0 response-integrity gate at both visitor JSON exits;
- immutable exact-query Gold Star answer authority;
- 114 approved Gold Star records and 112 active structural-learning contributors;
- governed qualitative transfer reviews;
- a conservative semantic shadow observer;
- seven held-out question classes and a live evaluation harness.

The following are known gaps to close:

1. **Integrity is not intellectual quality.** The current v2.0 gate checks answer presence, generic non-answer markers, markup, size, and query context. It does not establish factual accuracy, completeness, task fit, reasoning quality, or usefulness.
2. **Semantic observation is not enforcement or certification.** The current semantic evaluator is heuristic and intentionally shadow-only. Its phrase signals cannot certify meaning, and a heuristic pass cannot establish Gold Star quality.
3. **Question classification is too shallow for a universal floor.** The current semantic classifier uses a small ordered set of phrase patterns and reports high confidence for a match. It does not adequately represent multi-intent, domain, stakes, requested deliverable, evidence needs, or ambiguity.
4. **Paired path evidence is absent.** The seven-case LLM/deterministic fixture template has no captured outputs. Do not claim parity or production-wide Gold Star performance until real, attributable outputs are captured for both paths.
5. **Deterministic routes need explicit capability boundaries.** A deterministic route may use a governed exact answer or a purpose-built, tested recovery. It must not be treated as semantically equivalent to a capable LLM merely because it passes the same minimal envelope checks. If it cannot satisfy the task, it must not fabricate a complete answer.
6. **Question-specific evaluation is narrow.** Existing held-out checks are useful regression signals but several rely on phrase matching and a small seven-question sample. They do not yet establish broad, representative coverage.
7. **The repair loop is not yet a governed universal mechanism.** Corrections have often been made as isolated question-specific patches. Promote only reusable, evidence-supported contracts with positive and negative boundary tests.
8. **Quality evidence needs separation.** Runtime integrity checks, heuristic semantic signals, source-grounded factual verification, blind human review, and user-approved Gold Star elevation are distinct evidence classes and must not be conflated.

## 4. Runtime design requirements

### 4.1 One shared question contract

Create a versioned, source-independent question contract consumed by LLM composition, deterministic handlers, specialists, validators, and final response boundaries. The contract must be serializable, auditable, and safe to expose in non-sensitive diagnostics. It must not require visitor query or answer text to be logged.

### 4.2 One answer envelope

All completed answers use one structured envelope containing at least:
- originating query or a privacy-safe request correlation reference;
- response text;
- response source/provenance class;
- question-contract version and task classification;
- evidence/provenance references where relevant;
- validation outcome and applicable checks;
- repair attempt count/outcome;
- separate optional recommendation/doorway metadata;
- explicit completion, clarification, or abstention state.

Structured specialist handoffs and explicit error payloads retain their own contracts and are not misrepresented as completed answers.

### 4.3 Layered validation, not a single brittle semantic score

Separate:
- **Hard, objective invariants:** transport/schema integrity, explicit user constraints, unsafe output, missing deliverable, invalid or unverified links, exact-answer immutability, secret disclosure, required structured fields.
- **Evidence validation:** source support, factual claims, calculations, code/configuration verification, temporal validity, uncertainty, and attribution.
- **Question-specific adequacy:** whether the answer performs the requested task and meets its completion criteria.
- **Human quality assessment:** prose, structure, coherence, insight, proportionality, usefulness, and discernment where automated evidence is insufficient.

No phrase heuristic may hard-fail a response merely because a required phrase is absent. No semantic heuristic pass may certify an answer. Machine-enforce only defects with sufficiently reliable evidence and calibrated false-positive rates.

### 4.4 Bounded repair

For non-frozen responses only:
1. identify the precise failed criterion and evidence;
2. repair only the affected deficiency while preserving correct content and constraints;
3. re-run the relevant validators;
4. stop after a bounded number of attempts;
5. if still deficient, clarify, abstain, or disclose the limitation.

No infinite retry loops, silent content degradation, or provider-cost escalation. Frozen Gold Stars are immutable; a failed frozen record is withheld for governed review, never silently edited.

### 4.5 Answer and doorway integrity

The answer must satisfy the question before any doorway is considered. A doorway is optional, canonical, verified, contextually relevant, and useful. Explicit no-handoff instructions override recommendations. A title match alone is not sufficient evidence of relevance. Never invent a URL or substitute a generic menu destination.

## 5. Question-specific Gold Star elevation protocol

A response becomes a Gold Star only through separate, explicit approval. The protocol requires:

1. exact visitor question and actual rendered answer captured from a named runtime and commit;
2. task/domain/stakes and intended outcome identified;
3. review against all eight v2.0 dimensions, with non-applicable dimensions explained;
4. factual and source claims checked against appropriate evidence;
5. explicit assertions describing what makes the answer correct and complete;
6. verified doorway or an evidenced intentional omission;
7. qualifying context and abstention boundary for any transferable lesson;
8. positive tests and adversarial/negative tests to prevent over-transfer;
9. provenance, freeze policy, and exact-query authority recorded;
10. explicit user approval before Gold Star status or numbering changes.

A Gold Star is an approved exemplar and governed learning asset. It is not itself proof that every other query meets the quality floor.

## 6. Evaluation and measurement

### 6.1 Representative paired capture

Capture real outputs for the same held-out questions across LLM and deterministic routes where both routes are genuinely supported. Preserve raw output and runtime identity, commit/fingerprint, timestamps, request IDs, transport outcomes, and provenance. Never fabricate a missing path output or infer one path from the other.

### 6.2 Evaluation layers

- unit and contract tests for objective invariants;
- question-class and domain-specific regression tests;
- paired LLM/deterministic quality comparisons;
- adversarial tests for constraints, ambiguity, prompt injection, source conflict, stale evidence, and abstention;
- blinded human review using the eight dimensions;
- actual browser acceptance on primary and secondary after CI passes.

Parity means comparable task-appropriate quality and constraint adherence, not identical wording or identical response length. Report coverage and unsupported route combinations; do not hide missing fixtures.

### 6.3 Promotion criteria

Before production promotion:
- all relevant CI and regression workflows pass on the exact release commit;
- the registry and transfer-review inventories reconcile without altering existing approved records;
- actual paired fixtures exist for the routes claimed to be covered;
- independent human review finds no critical dimension failures in the representative sample;
- automated evaluator signals are calibrated against human decisions and false-positive/false-negative rates are reported;
- deterministic routes demonstrate honest capability limits;
- browser interaction confirms answer and doorway behavior on primary and secondary;
- deployment identity and post-deploy health are verified.

Do not claim universal Gold Star performance from seven cases, a clean CI run, a prompt instruction, a status log, or a heuristic pass.

## 7. Preservation and operational constraints

- Preserve the 114 approved Gold Star records, 112 active structural contributors, benchmark IDs, exact answer text, provenance, transfer boundaries, freeze policies, and numbering unless a separately approved record-specific change is made.
- Preserve all existing approved Gold Star answers as immutable.
- Do not turn the Gold Star standard into a rigid answer template or a forced Archive framing.
- Do not widen transfer authority from semantic similarity alone.
- Do not expose visitor query/answer content in diagnostic logs merely to prove activation.
- Do not make production changes, trigger duplicate deployments, or promote a branch before full CI, regression, and browser acceptance.
- Keep evaluation provider-free/offline where possible. Live captures must use existing primary/secondary services only after an explicit, bounded test plan; do not create new Render services or incur unnecessary provider/Pinecone usage.

## 8. Implementation sequence

**Phase 0 — Baseline and instrumentation audit:** map every answer route, identify bypasses, document provenance, verify both visitor boundaries, and capture current baseline behavior without changing production.

**Phase 1 — Shared question contract:** implement a versioned structured task contract, calibrated unknown/mixed-intent states, explicit-constraint precedence, and contract tests.

**Phase 2 — Composer and deterministic capability alignment:** make every supported source consume the same task contract and applicable completion criteria; remove generic deterministic pseudo-completion where no reliable answer exists.

**Phase 3 — Evidence-aware validation and bounded repair:** add layered validators, reliable hard-failure boundaries, non-enforcing review flags where semantics are uncertain, and bounded repair/clarification/abstention.

**Phase 4 — Real paired evaluation and calibration:** capture real LLM/deterministic outputs, expand held-out diversity, compare blinded human scores, and calibrate automated signals.

**Phase 5 — Question-specific elevation loop:** use each visitor-tested answer to correct the reusable contract first and the question-specific contract second; elevate only after evidence and explicit approval.

**Phase 6 — Controlled release:** complete all gates on an isolated branch; promote to primary and secondary only after the exact release candidate passes.

## 9. Definition of success

The system consistently produces a first response that is fit for the actual question, well reasoned, epistemically honest, complete enough for the requested outcome, clear, useful, and correctly bounded. It does so across supported answer sources without relying on repeated manual patching or a fixed template. When it cannot meet that standard, it handles the limitation transparently rather than presenting a weak answer as Gold Star quality.

**Governing principle:** Fix the generator, not just the generated answer. The quality floor must exist before the response is written, remain present while it is composed, and be verified before it reaches the visitor.
