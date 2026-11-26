# Objective-Integrity Gold Star — Groq GPT-OSS 20B Matched-Pair Pilot

**Pre-registration date:** 2026-11-26  
**Evaluation ID:** `gold-star-objective-integrity-heldout-pilot-groq-20b-2026-11-26`  
**Target benchmark:** `general-guide-developmental-stewardship-objective-integrity-2026-11-26`  
**Pinned provider/model:** Groq / `openai/gpt-oss-20b`

## Why this is a separate evaluation

The original Groq / `openai/gpt-oss-120b` attempt returned a model-scoped HTTP 429 (`provider_wide=false`) on its first control-arm request. The Gemini attempt returned a quota/billing rejection on its first control-arm request. The Workers AI attempt did not start because this repository's Actions runner has no Cloudflare credentials configured. None of those attempts reached a treatment arm or produced a valid pair.

This evaluation is a separate model-specific stratum on Groq GPT-OSS 20B. It is not a fallback within the earlier 120B pairs, and no results from prior attempts are pooled.

## Hypothesis and design

Enabling the approved objective-integrity Gold Star improves held-out answers about optimization, metrics, development and goal fitness by helping the Guide distinguish improving methods from reconsidering an objective, detect proxy drift and self-reinforcing incentives, account for unmeasured consequences, and respect legitimate decision authority.

- Six held-out questions across three transfer families: proxy/metric drift, incentive feedback loops, and goal fitness/revision.
- Same candidate-local ASGI `/api/query` boundary for both arms.
- Control disables Gold Star guidance; treatment enables it.
- Both arms are pinned to Groq `openai/gpt-oss-20b`.
- The runner filters every request to the exact provider/model. Sibling-model fallback is not admitted.
- Same runtime commit, base prompt, user message, schema, generation settings and timeout fingerprints are required.
- Call order is counterbalanced; blind A/B labels are independently randomized.
- 65-second spacing is retained; the provider bank is bounded to one attempt per request.
- One unrelated physical-science selector negative control checks that the target lesson is not over-triggered.

## Primary scoring and screening threshold

Independent reviewers score both responses while blind to treatment/control using the case-specific rubric and common `objective_integrity_reasoning` dimension. Hard gates are safety, evidence integrity and epistemic calibration.

- Mean treatment improvement of at least 0.25 on the 0–2 scale.
- At least two-thirds of valid pairs independently judged improved.
- No treatment hard-gate failures or critical-dimension zeros.
- Paired 95% Student-t interval lower bound above zero.

The six-case cohort is curated, not random. A positive pilot is preliminary comparative evidence only; it must be replicated on a later unseen cohort and prospective visitor requests before claiming durable or general visitor improvement.

## Interpretation limits

Retrieval is not selection. Provider selection is not semantic application. Exact-span presence is not semantic quality. Contribution retention is not measured benefit. Blind human review is mandatory and must precede unblinding. No Gold Star registry mutation or automatic promotion occurs.
