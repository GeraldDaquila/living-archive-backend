# Guide live-evaluation protocol

## Purpose

Capture actual responses from the running Guide API, score exact approved/frozen references and held-out generalization cases, and retain a reproducible report. The evaluation runs automatically twice daily and can also be invoked manually. It is a bounded synthetic benchmark replay, not a capture of ordinary visitor conversations. It never changes production.

## Schedule and workload

- GitHub Actions schedule: every 12 hours at minute 17 UTC.
- Each run submits the registry-selected General Guide questions and held-out cases to `POST /api/query`.
- The current selected workload is 26 approved/frozen General Guide benchmarks plus 3 held-out cases (29 requests per run); the script derives this set from the versioned registry and evaluation suite.
- Manual invocation remains available for primary or mirror.
- Reports are uploaded as 90-day artifacts. A failed critical check fails the run after the report is uploaded.

## Evidence captured

- Registry and evaluation-set SHA-256 hashes, registry file commit, and evaluated Git commit.
- Runtime version, fingerprint, and source hash reported by the service.
- Submitted synthetic question, HTTP status, request ID, returned answer, recommendation, answer-basis metadata, intent, and processing route.
- Per-case checks and an overall pass/fail summary, plus pending human-review scorecards.

## Acceptance rules

1. Select only General Guide records whose registry status is `USER_APPROVED_GOLD_STANDARD` or `FROZEN_REFERENCE_ONLY`. Never silently promote recovered records or candidates.
2. Exact-response checks apply only where approval/freeze metadata requires exact wording. Behavioral reference standards are scored on their recorded assertions, response shape, and doorway contract rather than treated as universal templates.
3. Check the answer and the recommendation separately. An exact answer does not excuse a wrong doorway; a correct doorway does not excuse a poor answer.
4. Held-out checks are bounded deterministic smoke checks, not a substitute for human judgment. Any Archive-specific factual claim still needs canonical-source review. No lesson is promoted automatically.
5. Any failed gold-standard check or held-out check fails the run. The uploaded report is retained even when the job fails.
6. The workflow has read-only repository permission, no deployment step, no WordPress write step, no provider-key requirement, and no path to modify `use_core.py`.
7. Synthetic reports contain the benchmark questions and responses needed for review. They do not include ordinary visitor conversation data.

## Production visitor-answer monitoring: not yet implemented

This scheduled workflow evaluates known synthetic questions against the live service. It does **not** sample, retain, or score actual visitor conversations. Production interaction monitoring requires a separately reviewed design covering consent/notice, data minimization, sensitive-content exclusion, retention/deletion, access controls, and aggregation. Do not enable raw visitor transcript collection as a shortcut.

## Interpretation

A passing run means the declared automated checks passed for the captured runtime identity. It does not prove universal answer quality, that all Archive claims are grounded, or that ordinary visitor answers are satisfactory. A failure is actionable evidence: preserve the response, request ID, runtime fingerprint, failing rubric, and registry identity before proposing a fix. Human review remains required for substantive quality judgments and any lesson promotion.
