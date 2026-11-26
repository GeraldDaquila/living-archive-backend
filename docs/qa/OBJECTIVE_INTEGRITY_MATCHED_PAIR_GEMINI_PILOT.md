# Objective-Integrity Gold Star — Gemini Matched-Pair Pilot

**Pre-registration date:** 2026-11-26  
**Evaluation ID:** `gold-star-objective-integrity-heldout-pilot-gemini-2026-11-26`  
**Target benchmark:** `general-guide-developmental-stewardship-objective-integrity-2026-11-26`  
**Pinned provider/model:** Gemini / `gemini-3.8-flash`

## Why this is a separate evaluation

The first pre-registered Groq / `openai/gpt-oss-120b` attempt returned HTTP 429 on its first control-arm request. The runner stopped before the treatment arm and produced zero valid pairs. No alternate provider was substituted into those pairs. This Gemini run has a separate evaluation ID and must not be pooled with the failed Groq attempt.

## Hypothesis

Enabling the approved objective-integrity Gold Star improves held-out answers about optimization, metrics, development and goal fitness by helping the Guide distinguish improving methods from reconsidering an objective, detect proxy drift and self-reinforcing incentives, account for unmeasured consequences, and respect legitimate decision authority.

## Design

- Six held-out questions across three transfer families: proxy/metric drift, incentive feedback loops, and goal fitness/revision.
- Same candidate-local ASGI `/api/query` boundary for both arms.
- Control disables Gold Star guidance; treatment enables it.
- Both arms use the exact pinned Gemini model `gemini-3.8-flash`.
- Same runtime commit, base prompt, generation settings, token budget, schema and timeout fingerprints are required.
- The actual Gemini payload is fingerprinted separately from Groq: temperature is recorded as provider default because it is not supplied; thinking level is low; JSON MIME/schema behavior is recorded; schema hash is calculated after Gemini's compatibility transformation.
- Call order is counterbalanced; blind A/B labels are independently randomized.
- 65-second spacing is retained; no provider fallback or model substitution is allowed.
- One unrelated physical-science selector negative control checks that the target lesson is not over-triggered.

## Primary scoring

Independent reviewers score both responses while blind to treatment/control using the case-specific rubric and a common `objective_integrity_reasoning` dimension. Additional dimensions cover directness, factual accuracy, proxy/purpose alignment, feedback loops, unmeasured consequences, method-versus-goal judgment, affected-party authority, calibration and usefulness.

Hard gates: safety, evidence integrity and epistemic calibration. A failed hard gate blocks improvement credit.

## Pre-registered screening threshold

- Mean treatment improvement of at least 0.25 on the 0–2 scoring scale.
- At least two-thirds of valid pairs independently judged improved.
- No treatment hard-gate failures or critical-dimension zeros.
- The paired 95% Student-t uncertainty interval must have a lower bound above zero.

The six-case cohort is curated, not a random sample of all visitor traffic. A positive result is preliminary comparative evidence only. It must be replicated on a later unseen cohort and prospective visitor requests before claiming durable or general visitor improvement.

## Interpretation limits

Retrieval is not selection. Provider selection is not proof of semantic application. Exact-span presence is not semantic quality. Final-answer delivery is not contribution retention. Contribution retention is not measured benefit. Blind human review is mandatory, and scoring must be completed before unblinding. The six-pair pilot is a screening experiment, not final adaptive-engine certification.

No Gold Star registry mutation or automatic promotion occurs. The approved lesson is frozen; this pilot evaluates its runtime transfer only.
