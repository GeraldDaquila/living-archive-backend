# Adaptive Improvement: Evidence and Acceptance Protocol

## The question this protocol answers

Does enabling the Adaptive Learning Engine make ordinary Guide answers measurably better, more consistently, on future questions than the same system operating without the learned contribution?

A good answer, a successful deployment, a passing deterministic Gold Standard test, or a retrieved Gold Star is not by itself evidence of adaptive improvement.

## Evidence levels

1. **Answer-quality observation** — one answer appears strong under a stated rubric. Useful for diagnosis; not causal evidence.
2. **Application evidence** — a request-level trace proves that a specific approved Gold Star was selected, injected into the relevant composition path, retained in the final answer, and not merely retrieved, cached, or supplied by deterministic fallback.
3. **Comparative improvement evidence** — matched held-out questions are answered with adaptive learning enabled and disabled under comparable conditions; independent blind scoring shows a pre-specified practically meaningful improvement with uncertainty reported.
4. **Prospective visitor evidence** — the effect persists on later unseen visitor queries, with no unacceptable regressions in safety, factuality, relevance, abstention, latency, or reliability.

## Required experiment

- Freeze the candidate Gold Star version, runtime configuration, evaluation rubric, query cohort, exclusions, and primary outcome before the run.
- Build a held-out set of realistic questions that qualify for the lesson, with paraphrases and transfer cases that do not repeat the approved exemplar wording.
- Include unrelated negative-control questions to detect over-triggering or degradation outside the lesson's scope.
- Run matched pairs: the same question under adaptive-learning ON and OFF. Randomize run order and balance provider/model, temperature, token/time budgets, retrieval context, and other material conditions as far as technically possible. Record unavoidable differences.
- Preserve per-request traces. For ON runs, capture benchmark ID/version, selector decision, contribution payload/hash, composition injection, final-answer retention assessment, provider/model invocation, fallback/cache disposition, and final request ID. For OFF runs, prove the contribution was absent.
- Blind independent raters to condition and score a pre-registered rubric: correctness, relevance, reasoning quality, calibration/uncertainty, safety, and task usefulness. Record individual scores and inter-rater agreement.
- Calculate paired differences, effect size, confidence interval, sample size/power rationale, and any multiple-comparison adjustments. Set the minimum practically meaningful improvement threshold before seeing results; do not choose it after observing scores.
- Report all failures and adverse movements, including factuality, unsupported claims, safety, irrelevant Gold Star injection, refusals, provider exhaustion, latency, and user task completion where measurable.
- Repeat with a later unseen cohort or prospective visitor sample. A one-time benchmark win is not enough to claim durable learning.

## Acceptance decision

Claim **attributable application** only when request-level evidence closes the full selection-to-retention chain.

Claim **measured adaptive improvement** only when the pre-registered matched-pair held-out evaluation shows a practically meaningful positive effect with an uncertainty interval supporting improvement, attribution traces are complete, and negative controls show no material regressions.

Claim **durable visitor improvement** only after the effect replicates on a later unseen or prospective visitor cohort and visitor-relevant outcomes are measured.

If any gate is missing, report the highest evidence level actually achieved. Do not substitute retrieval success, deterministic answer delivery, provider invocation, one strong screenshot, or a high subjective rating for application or outcome evidence.
