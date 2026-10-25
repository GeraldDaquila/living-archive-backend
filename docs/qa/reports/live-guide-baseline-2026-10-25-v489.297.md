# Live Guide baseline probe — 2026-10-25

**Status:** captured production evidence; two held-out failures confirmed.  
**Method:** Cowboy MCP wp_http_request POST to the public production /api/query endpoint. The WordPress Guide page also returned HTTP 200 during the same session.  
**This is a first manual probe, not the output of the new GitHub Actions runner.**

## Runtime and baseline identity

- Service: https://living-archive-backend.onrender.com
- Runtime version: v489.297
- Fingerprint: USE-v489.297-human-voice-conceptual-fallback
- Runtime source SHA-256 reported by API: b48da54b9d6bb379349451ab152c64c7f9d1acb6e553b127dadc22444292a082
- Registry GitHub blob SHA: 91a00cf35f97c62ae110f4f58068660bd9702464
- Evaluation suite: living-archive-guide-learning-offline-evaluation, version 1.0.0
- API response timestamp: 2026-10-25 03:32 UTC (from response headers)
- Protected core: no edits; no production deployment made by this probe.

## Results

| Set | Result | Interpretation |
|---|---:|---|
| Registry-selected gold standards | 8/8 | All eight exact questions returned the registered response text. Registered doorway/no-doorway behavior was also observed as expected. |
| Held-out generalization cases | 1/3 passed | Two cases fail the intended generalization contract. |
| Transport | 11/11 HTTP 200 | HTTP success did not imply answer quality. |

### Gold-standard request IDs

| Benchmark | Request ID | Observed |
|---|---|---|
| general-guide-stewardship-gold-standard-2026-10-14 | basic-ec47bc29297f891f | Exact answer; no doorway, as requested. |
| general-guide-reciprocity-gold-standard-2026-10-19 | basic-0b155fc0cad05590 | Exact answer; registered reciprocity doorway. |
| general-guide-practical-trust-application-2026-10-22 | basic-731a795be23a898d | Accepted response text; no unsolicited doorway. |
| general-guide-conceptual-accountability-trust-harm-repair-2026-10-22 | basic-c3d891024b8dec8c | Accepted response text; no unsolicited doorway. |
| general-guide-human-development-significance-2026-10-24 | basic-7b65a5fcababbb16 | Exact answer; registered doorway. |
| general-guide-water-boiling-point-general-knowledge-gold-standard-2026-10-24 | basic-8deaea5cd795717c | Exact concise general-knowledge answer; no doorway. |
| general-guide-living-archive-cosmology-gold-standard-2026-10-25 | basic-25796ab676910caf | Exact three-paragraph Archive cosmology answer; registered doorway. |
| general-guide-first-principles-gold-standard-2026-10-25 | basic-36f447825e84c2a8 | Exact three-paragraph answer; all six principles and registered doorway present. |

## Held-out results

### 1. Water boiling point — FAIL

- Case: heldout-water-boiling-point-001
- Request ID: basic-c00d0864b8b3df6c
- Query: “At standard atmospheric pressure, what temperature does water boil at?”
- Response began: “The question about At standard atmospheric pressure, what temperature does water boil at deserves a direct answer, not a guess presented as certainty.”
- It did not state 100°C or 212°F, used a generic uncertainty/investigation prompt, and attached the unrelated [LSW-001] Leader Standard Work doorway.
- Root cause found in source inspection: the existing established-fact matcher recognized “boiling point” wording but not the equivalent “what temperature does water boil at?” form. A separate runtime PR adds the paraphrase regression and matcher fix.

### 2. Cosmology and lived significance — FAIL

- Case: heldout-cosmology-life-001
- Request ID: basic-efff36a6acc5d2be
- Query: “What is cosmology, and why does it matter to how people live?”
- Response began: “To understand why cosmology, and why does it matter to how people live, separate the immediate event from the conditions that made it more likely.”
- It failed to define cosmology or connect it to human life and instead returned an unrelated recurring-problem diagnostic template with an unrelated doorway.
- Root cause found in source inspection: the conceptual classifier recognized “What is the cosmology of the Living Archive?” but not the broader compound form “What is cosmology, and why does it matter?”. A separate runtime PR adds a generalized compound-question routing rule and regression test.

### 3. Practical trust — BOUNDED CHECKS PASS; provenance requires review

- Case: heldout-practical-trust-001
- Request ID: basic-6f60240675d4d32e
- The answer gave concrete organizational actions and no unsolicited doorway; it matched the accepted practical-trust response.
- The answer_basis metadata labelled the answer “General knowledge” and said no sufficiently relevant Archive resource was identified. This is not proof of a false attribution—the label does not claim the text came from the Archive—but the provenance signal should be reviewed separately against the source/evaluation policy.

## Decision

- Preserve all eight positive references as the non-regression floor.
- Keep the two failed held-out cases as blocking generalization checks until the fixes pass automated tests and a post-deployment live probe.
- Do not promote a lesson or claim the Guide is “learning” from this single probe.
- The manual evaluation runner in this PR family will preserve the complete response, recommendation, answer-basis metadata, request ID, runtime fingerprint, and registry/suite identity on each run.
- No changes to use_core.py, no WordPress content writes, and no deployment occurred during this probe.
