# Objective-Integrity Gold Star — Cloudflare Workers AI Matched-Pair Pilot

**Pre-registration date:** 2026-11-26  
**Evaluation ID:** `gold-star-objective-integrity-heldout-pilot-workers-ai-2026-11-26`  
**Target benchmark:** `general-guide-developmental-stewardship-objective-integrity-2026-11-26`  
**Pinned provider/model:** Cloudflare Workers AI / `@cf/zai-org/glm-4.7-flash`

## Why this is a separate evaluation

The first pre-registered Groq / `openai/gpt-oss-120b` attempt returned HTTP 429 on its first control-arm request. The second Gemini / `gemini-3.8-flash` attempt returned a quota/billing rejection on its first control-arm request. Neither attempt reached a treatment arm or produced a valid pair. This is a new provider-specific evaluation ID; no outputs or scores from those failed attempts are pooled here.

## Hypothesis and design

The hypothesis and six held-out questions are unchanged: enabling the approved objective-integrity Gold Star should improve transfer to questions about proxy/metric drift, incentive feedback loops, and goal fitness/revision.

- Six held-out questions across three transfer families.
- Same candidate-local ASGI `/api/query` boundary for both arms.
- Control disables Gold Star guidance; treatment enables it.
- Both arms are pinned to Cloudflare Workers AI `@cf/zai-org/glm-4.7-flash`.
- The runner filters the provider bank to the exact provider/model for every paired request. Sibling-model fallback is not admitted, so both arms cannot silently switch models.
- Same runtime commit, base prompt, user message, schema, generation settings and timeout fingerprints are required.
- Call order is counterbalanced; blind A/B labels are independently randomized.
- 65-second spacing is retained. The provider bank is bounded to one attempt per request.
- One unrelated physical-science selector negative control checks that the target lesson is not over-triggered.

## Actual Workers AI payload fingerprint

The runner records `max_tokens`, `temperature=0.0`, JSON response-format mode and effective schema hash, `options.rejectIfBusy=true`, the `_workers_normalize_messages` adapter, provider timeout, and the single HTTP-attempt policy. It does not reuse Groq or Gemini settings in the fingerprint.

## Primary scoring and screening threshold

Independent reviewers score both responses while blind to treatment/control using the case-specific rubric and common `objective_integrity_reasoning` dimension. Hard gates are safety, evidence integrity and epistemic calibration.

- Mean treatment improvement of at least 0.25 on the 0–2 scale.
- At least two-thirds of valid pairs independently judged improved.
- No treatment hard-gate failures or critical-dimension zeros.
- Paired 95% Student-t interval lower bound above zero.

The six-case cohort is curated, not random. A positive pilot is preliminary comparative evidence only; it must be replicated on a later unseen cohort and prospective visitor requests before any durable visitor-improvement claim.

## Interpretation limits

Retrieval is not selection. Provider selection is not semantic application. Exact-span presence is not semantic quality. Contribution retention is not measured benefit. Blind human review is mandatory and must precede unblinding. No Gold Star registry mutation or automatic promotion occurs.
