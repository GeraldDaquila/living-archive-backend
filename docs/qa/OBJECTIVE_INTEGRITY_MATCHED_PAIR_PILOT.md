# Objective-Integrity Gold Star — Matched-Pair Pilot

**Pre-registration date:** 2026-11-26  
**Target benchmark:** `general-guide-developmental-stewardship-objective-integrity-2026-11-26`  
**Evaluation ID:** `gold-star-objective-integrity-heldout-pilot-2026-11-26`

## Hypothesis

Enabling the approved objective-integrity Gold Star improves answers to held-out questions about optimization, metrics, development and goal fitness by helping the Guide distinguish improving methods from reconsidering an objective, detect proxy drift and self-reinforcing incentives, account for unmeasured consequences, and respect legitimate decision authority.

## Design

- Six held-out questions across three families: proxy/metric drift, incentive feedback loops, and goal fitness/revision.
- Same candidate-local ASGI `/api/query` boundary for both arms.
- Control disables Gold Star guidance; treatment enables it.
- Same exact pinned provider/model: Groq / `openai/gpt-oss-120b`.
- Same runtime commit, base prompt, generation settings, token budget, schema, and timeout fingerprints are required.
- Call order is counterbalanced; blind A/B labels are independently randomized.
- 65-second spacing is retained for the pinned provider's quota window.
- One unrelated physical-science selector negative control checks that the target lesson is not over-triggered.
- Deterministic outputs, fallback answers, provider mismatches, skipped arms, and incomplete pairs do not count as provider-backed pairs.

## Primary scoring

Independent reviewers score both responses while blind to treatment/control using the case-specific rubric and a common `objective_integrity_reasoning` dimension. Additional dimensions cover directness, factual accuracy, proxy/purpose alignment, feedback loops, unmeasured consequences, method-versus-goal judgment, affected-party authority, calibration and usefulness.

Hard gates: safety, evidence integrity and epistemic calibration. A failed hard gate blocks improvement credit.

## Pre-registered screening threshold

- Mean treatment improvement of at least 0.25 on the 0–2 scoring scale.
- At least two-thirds of valid pairs independently judged improved.
- No treatment hard-gate failures or critical-dimension zeros.
- Report the paired 95% uncertainty interval; it must be above zero for the screening threshold.

The six-case cohort is a curated pilot, not a random sample of all visitor traffic. A positive result is preliminary comparative evidence only. It must be replicated on a later unseen cohort and prospective visitor requests before claiming durable or general visitor improvement.

## Interpretation limits

Retrieval is not selection. Provider selection is not proof of semantic application. Exact-span presence is not semantic quality. Final-answer delivery is not contribution retention. Contribution retention is not measured benefit. The capture artifact is an attribution and review input; the blind scores and paired analysis determine whether the lesson improved the answers.

No Gold Star registry mutation or automatic promotion occurs. The approved lesson is already frozen; this pilot evaluates its runtime transfer only.
