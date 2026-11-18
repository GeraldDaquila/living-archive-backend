# Gold Star response floor: cross-path investigation

**Date:** 2026-11-19  
**Status:** Investigation finding; implementation changes beyond the exact-question benchmark are not yet authorized by evidence.

## Executive finding

Gold Star quality can and should be the minimum quality target for both LLM-generated and deterministic visitor answers. It must be a shared, source-independent acceptance standard. The answer's generation method must not lower the visitor-facing standard.

The current system does not yet demonstrate that this is true. The existing `gold_star_response_floor.py` is a shared transport-boundary gate, but it verifies response integrity rather than substantive quality. A short, generic, question-irrelevant sentence can pass. Therefore the current implementation is a minimum non-empty-answer safeguard, not a Gold Star quality floor.

## What is already in place

1. `gold_star_response_floor.py` v2.0 is invoked from both the shared JSON sender and the outer final visitor boundary in `main.py`. It is source-independent and therefore can inspect LLM, exact Gold Star, deterministic fallback, and specialist answer payloads.
2. It rejects missing answers, generic non-answer markers, unsafe markup, over-limit content, and missing query context. It preserves frozen exact Gold Star content and exempts structured handoffs to their own contracts.
3. `docs/qa/gold_standard_registry.json` is the version-controlled benchmark authority. Approved and frozen records are selected as acceptance baselines; recovered/candidate records are not silently promoted.
4. `docs/qa/guide_learning_evaluation_set.json` already provides held-out cases across general facts, conceptual explanation, practical application, strategic trade-offs, technical verification, uncertainty/insufficient evidence, and explicit no-handoff behavior. Its human review rubric includes answer directness, accuracy, provenance, human voice, coherence, proportionality, uncertainty, doorway relevance, and visitor orientation.
5. Existing policy explicitly says automated checks are triage, not semantic approval. Human review is required for applicable dimensions, Archive-specific claims, and any lesson promotion.

## Critical gap

The current response-floor gate does not evaluate whether the answer:
- responds to the actual question rather than merely containing text;
- contains the essential reasoning or distinctions required by the question type;
- is factually accurate and proportionate to available evidence;
- preserves Archive source boundaries and provenance;
- uses a doorway only when relevant, verified, optional, and properly timed;
- avoids generic, circular, or superficially polished but empty language.

A simple shared gate cannot safely enforce these semantic properties through length, paragraph count, keywords, or one universal answer template. Those shortcuts would reward verbosity, misclassify concise factual answers, and break valid exceptions such as explicit no-handoff requests, navigation-only requests, specialist handoffs, and questions for which no doorway is warranted.

## Recommended architecture

Use a layered quality floor, applied identically to every completed answer regardless of provenance:

### Layer 1 — Universal hard invariants (automated, source-independent)
- non-empty answer and valid request context;
- safe output and payload structure;
- no generic non-answer when a substantive answer is expected;
- no unsupported claims of retrieval, citation, or Archive authority;
- provenance and answer-basis fields are internally consistent;
- no fabricated or unverified doorway;
- explicit user constraints (including no-link/no-handoff) are preserved;
- structured handoffs and safety/error responses use their own contracts.

### Layer 2 — Question-sensitive composition and reasoning contracts (automated assertions)
Classify the task before evaluating it. Use the same contracts for LLM and deterministic outputs, but vary the assertions by question type: factual, conceptual, practical, strategic/trade-off, technical, uncertainty-limited, personal/lived, navigation-only, explicit no-handoff, and specialist handoff. Assertions should test required distinctions and failure modes, not force identical wording or length.

### Layer 3 — Benchmark and held-out evaluation (automated regression + human semantic review)
Run exact-query Gold Star/frozen references and held-out cases against both output paths. Preserve negative controls and intentional exceptions. A candidate must not pass by improving one family while regressing another. Human review scores applicable rubric dimensions; no critical zero, unsupported Archive-specific claim, or approved-standard regression is acceptable.

### Layer 4 — Release decision and monitoring
Record commit, runtime identity, output provenance, question family, benchmark set, path (LLM/deterministic), score, critical failures, and regressions. Do not claim a universal floor is proven until representative paired evaluations show both paths meet it.

## Evaluation design

For each held-out question, obtain a valid LLM answer and a deterministic answer where a supported deterministic route exists. Score both against the same question-specific rubric, blinded to generation source where practical. Report:
- coverage and denominator by question family and generation path;
- critical-failure rate and reason;
- applicable-dimension score distribution;
- doorway correctness and omission compliance;
- uncertainty/provenance errors;
- exact Gold Star regressions and held-out transfer results;
- abstentions and structured handoffs separately.

Do not fabricate deterministic answers for question types without a deterministic route. Mark unsupported path/case combinations as not applicable and report coverage gaps rather than silently dropping them. Do not use live provider calls or Pinecone egress for this initial investigation; offline fixtures and existing CI are sufficient to build the evaluation contract.

## This elevation

The felt-truth discernment answer is approved as a question-specific Gold Star benchmark. Its step 3 uses evidence standards appropriate to the claim type; repeatability is not treated as a universal requirement. The exact answer, doorway, rationale, assertions, and transfer boundaries are frozen in the registry and fixture.

This exact-question elevation does **not** certify that all LLM or deterministic responses currently meet Gold Star quality. That system-wide claim remains an open validation target.

## Next engineering sequence

1. Complete CI for the new exact-question benchmark and registry/fixture consistency checks.
2. Build paired offline evaluation over the existing held-out set and expand coverage where a question family or path is missing.
3. Add source-independent, question-sensitive quality assertions at the shared final boundary; do not add brittle global length or three-paragraph rules.
4. Run regression suites across all approved/frozen Gold Stars, negative controls, LLM fixtures, deterministic fixtures, and explicit exception cases.
5. Only after tests and human review pass, consider deployment. Browser acceptance remains a separate live-surface validation gate.

## Resource and deployment constraints

This investigation must preserve the temporary Pinecone bypass through 2026-12-01. No Pinecone reactivation, re-indexing, egress-heavy testing, new Render services, paid upgrades, or unnecessary live provider simulations are required. Any production deployment must preserve the coordinated primary/secondary 70:30 architecture and use the established CI-before-deploy process.
