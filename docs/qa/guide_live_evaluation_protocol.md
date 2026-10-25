# Guide live-evaluation protocol

## Purpose

Capture actual responses from the running Guide API, score exact approved/frozen references and held-out generalization cases, and retain a reproducible report. This workflow is manual-only: it is not part of deploy, build, or pull-request validation and never changes production.

## Run

Open **GitHub → Actions → Guide Live Evaluation → Run workflow**. Choose `primary` or `mirror`. The workflow submits the registry-selected General Guide questions and the held-out cases to `POST /api/query`, then uploads the full JSON report as a 90-day artifact.

## Evidence captured

- Registry and evaluation-set SHA-256 hashes, registry file commit, and evaluated Git commit.
- Runtime version, fingerprint, and source hash reported by the service.
- Submitted question, HTTP status, request ID, returned answer, recommendation, answer-basis metadata, intent, and processing route.
- Per-case checks and an overall pass/fail summary.

## Acceptance rules

1. Select only General Guide records whose registry status is `USER_APPROVED_GOLD_STANDARD` or `FROZEN_REFERENCE_ONLY`. Never silently promote recovered records or candidates.
2. Exact-response checks apply only where approval/freeze metadata requires exact wording. Behavioral reference standards are scored on their recorded assertions, response shape, and doorway contract rather than treated as universal templates.
3. Check the answer and the recommendation separately. An exact answer does not excuse a wrong doorway; a correct doorway does not excuse a poor answer.
4. Held-out checks are bounded deterministic smoke checks, not a substitute for human judgment. Any Archive-specific factual claim still needs canonical-source review. No lesson is promoted automatically.
5. Any failed gold-standard check or held-out check fails the manual run. The uploaded report is retained even when the job fails.
6. The workflow has read-only repository permission, no deployment step, no WordPress write step, no provider-key requirement, and no path to modify `use_core.py`.

## Interpretation

A passing run means the declared automated checks passed for the captured runtime identity. It does not prove universal answer quality or that all Archive claims are grounded. A failure is actionable evidence: preserve the response, request ID, runtime fingerprint, failing rubric, and registry identity before proposing a fix.
