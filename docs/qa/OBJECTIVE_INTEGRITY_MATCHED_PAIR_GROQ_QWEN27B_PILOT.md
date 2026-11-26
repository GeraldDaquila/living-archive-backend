# Objective-Integrity Gold Star — Groq Qwen 3.8 27B Matched-Pair Pilot

**Pre-registration date:** 2026-11-26  
**Evaluation ID:** `gold-star-objective-integrity-heldout-pilot-groq-qwen27b-2026-11-26`  
**Target benchmark:** `general-guide-developmental-stewardship-objective-integrity-2026-11-26`  
**Pinned provider/model:** Groq / `qwen/qwen3.8-27b`

## Why this is a separate evaluation

The Groq GPT-OSS 120B and 20B attempts each returned a model-scoped HTTP 429 (`provider_wide=false`) on the first control-arm request. The Gemini attempt returned a quota/billing rejection. The Workers AI attempt could not start because Cloudflare credentials are not configured in this repository's Actions runner. None produced a valid pair or reached treatment. This is a separate Groq Qwen 3.8 27B model-specific stratum; no outputs or scores from previous attempts are pooled.

## Hypothesis and design

Enabling the approved objective-integrity Gold Star improves held-out answers about optimization, metrics, development and goal fitness by helping the Guide distinguish improving methods from reconsidering an objective, detect proxy drift and self-reinforcing incentives, account for unmeasured consequences, and respect legitimate decision authority.

- Six held-out questions across three transfer families.
- Same candidate-local ASGI `/api/query` boundary for both arms.
- Control disables Gold Star guidance; treatment enables it.
- Both arms are pinned to Groq `qwen/qwen3.8-27b`.
- Exact provider/model selection is enforced for every request; sibling fallback is excluded.
- Same runtime commit, base prompt, user message, schema, generation settings and timeout fingerprints are required.
- Call order is counterbalanced; blind A/B labels are independently randomized.
- 65-second spacing is retained; one provider attempt per request.
- One unrelated physical-science selector negative control checks that the target lesson is not over-triggered.

## Effective Qwen payload

The Provider Bank caps Qwen completion at 1,000 tokens. The runner now fingerprints the **effective** token ceiling (1,000, not the higher requested budget), `temperature=0.0`, JSON schema mode and effective schema hash, `reasoning_effort=none`, `reasoning_format=hidden`, provider timeout and the one-model/no-fallback policy. A response that cannot meet the visitor contract within the 1,000-token cap is a failed pair, not silently repaired into a success.

## Primary scoring and screening threshold

Independent reviewers score both responses while blind to treatment/control using the case-specific rubric and common `objective_integrity_reasoning` dimension. Hard gates are safety, evidence integrity and epistemic calibration.

- Mean treatment improvement of at least 0.25 on the 0–2 scale.
- At least two-thirds of valid pairs independently judged improved.
- No treatment hard-gate failures or critical-dimension zeros.
- Paired 95% Student-t interval lower bound above zero.

The six-case cohort is curated, not random. A positive pilot is preliminary comparative evidence only; it must be replicated on a later unseen cohort and prospective visitor requests before claiming durable or general visitor improvement.

## Interpretation limits

Retrieval is not selection. Provider selection is not semantic application. Exact-span presence is not semantic quality. Contribution retention is not measured benefit. Blind human review is mandatory and must precede unblinding. No Gold Star registry mutation or automatic promotion occurs.
