# The Guide — Dual-Path Quality Contract

**Status:** normative architecture contract  
**Scope:** primary LLM-first reasoning path and deterministic resilience path  
**Non-goals:** replacing LLM reasoning with rules; changing protected `use_core.py`; modifying the frozen HRN-LLM branch; changing WordPress administration (Cowboy MCP remains sole authority).

## 1. Architectural invariant

The Guide is LLM-first. The LLM path is the primary reasoning engine; deterministic recovery is a bounded resilience path used when the primary path is unavailable, times out, or fails response validation. The deterministic path is a **quality floor, not a reasoning ceiling**.

Do not route all questions through deterministic recovery merely because it is easier to test. Do not downgrade a valid LLM answer to a generic rule-based answer solely to make outputs look alike.

## 2. Shared minimum response contract

Both paths must preserve these invariants:

1. **Intent preservation:** answer the visitor's actual question and do not silently replace it with a neighboring topic.
2. **Evidence honesty:** distinguish Archive-supported claims from general knowledge, interpretation, and uncertainty. Never imply a canonical source supports a claim unless the retrieved evidence is sufficiently relevant.
3. **Resource relevance:** recommend a canonical resource only when evidence supports a direct relationship to the question. Empty doorway/resource is preferable to an irrelevant recommendation.
4. **Useful boundedness:** when evidence or provider capacity is insufficient, give a bounded answer if safe and appropriate; otherwise state the limitation and offer a useful next step. Do not promise a response and then issue a generic refusal.
5. **No fabricated certainty:** mark hypotheses as hypotheses; do not present plausible mechanisms as verified country-specific facts.
6. **Question boundaries:** specialist routing and fallback rules must not capture unrelated factual or conversational questions.
7. **Output integrity:** validate the assembled final response, not only an intermediate model output, because later stages can reattach an unsupported doorway or alter provenance.

## 3. Primary LLM path

The primary path should retain flexible interpretation and reasoning, retrieval over canonical evidence, synthesis across relevant resources, and context-sensitive composition. Before returning a response, validate the shared minimum response contract. An LLM provider returning HTTP success is not evidence of answer quality.

The LLM may exceed the deterministic reference by adding justified nuance, competing explanations, cross-resource synthesis, prioritization, and evidence-backed actions. It must not trade away the shared invariants to do so.

## 4. Deterministic resilience path

The deterministic path should provide explicit, bounded recovery for known classes of questions and provider failures. Every recovery rule must:
- be narrow enough not to hijack unrelated questions;
- preserve the user's core intent;
- state when it is giving general guidance rather than Archive-derived evidence;
- suppress unsupported resources/doorways;
- have positive and negative-control regression tests.

Deterministic coverage is not a claim that every possible question can be answered without an LLM.

## 5. Comparative QA — the deterministic floor and LLM enhancement

Maintain one versioned calibration corpus containing:
- ordinary questions and factual negative controls;
- nuanced, multi-part questions;
- Archive-grounding and resource-relevance cases;
- provider timeout/exhaustion cases;
- ambiguous questions and explicit uncertainty cases;
- known regressions from production.

For each case, evaluate both paths when feasible. Score separately: (a) intent preservation, (b) factual/evidence grounding, (c) causal reasoning, (d) completeness and usefulness, (e) resource relevance, (f) uncertainty calibration, and (g) response-contract compliance.

The LLM path is not required to copy the deterministic wording. It must satisfy every hard invariant and should improve depth/usefulness on cases requiring synthesis. A higher aggregate score cannot compensate for a hard failure such as fabricated evidence or an irrelevant canonical recommendation.

Any fix must rerun previously passing tests plus positive and negative controls. Test deterministic fallback directly under simulated provider failure; test LLM-first behavior separately under normal operation. Do not use browser-initiated visitor tests until simulated requests show a stable, grounded, non-leaking pipeline.

## 6. Release gates

A release is **NO-GO** if any of these remain unverified:
1. Relevant CI/regression workflows have completed successfully for the exact candidate commit.
2. The LLM-first path remains primary and existing routing contracts pass.
3. Deterministic recovery tests pass, including unrelated-question negative controls.
4. Final assembled responses preserve provenance and do not reattach unsupported doorways.
5. Primary and mirror deployments are live on the same intended commit.
6. Simulated live API calibration and negative-control requests pass on both services.
7. No protected file, frozen HRN-LLM branch, or WordPress surface was changed without separate authorization.

CI success permits deployment; it does not, by itself, prove live end-to-end readiness. Report the exact commit and separate CI, deployment, and live-response status.

## 7. Change discipline

Keep the LLM-first and deterministic implementations structurally distinct. Share contracts and test criteria; do not force both paths into one reasoning implementation. Changes to either path require regression tests against the shared corpus. Changes to protected `use_core.py` or frozen HRN-LLM behavior are outside this contract and require a separately scoped decision.
