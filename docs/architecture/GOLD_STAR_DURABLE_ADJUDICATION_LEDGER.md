# Gold Star Durable Adjudication Ledger — Architecture Contract

Status: Proposed implementation contract
Date: 2026-11-22
Scope: Independent, durable Gold Star candidate adjudication after visitor response delivery

## 1. Purpose

Separate the learning decision from visitor-facing answer composition. Deterministic recovery remains a dependable answer path. A Gold Star adjudication is a distinct, auditable operation that may run after the response has been delivered, subject to candidate eligibility, evidence availability, and protected provider capacity.

This ledger is not the Gold Star Registry. It records work and adjudication evidence; it does not itself authorize promotion.

## 2. Non-goals

- Do not replace or weaken deterministic answer recovery.
- Do not conflate factual claim adjudication with Gold Star candidate adjudication.
- Do not let a provider response automatically promote a Gold Star.
- Do not persist visitor question or answer text, user identity, session identity, or raw prompt content in the ledger.
- Do not claim global provider capacity reservation from process-local counters.
- Do not add an unbounded queue, unbounded retry loop, or visitor-request blocking dependency.

## 3. Operation boundaries

Three distinct operations must remain separately identified in telemetry and storage:

1. Guide composition: generates a candidate visitor response; may be provider-backed or deterministic.
2. Gold Star candidate adjudication: assesses whether a retrieved candidate lesson should be selected and applied to the actual delivered answer, including applicability boundaries and evidence.
3. Claim adjudication: separately assesses factual claims against retrieved visitor-visible public evidence.

A claim-adjudication result is never evidence that a Gold Star lesson was selected, applied, or beneficial.

## 4. Durable work record

The durable record should contain only privacy-minimized operational metadata:

- job_id: opaque UUID, primary key.
- request_id: existing opaque 32-character correlation token; unique with adjudication kind.
- attempt_ordinal: bounded positive integer.
- candidate_set_fingerprint: keyed or otherwise non-reversible fingerprint of canonical candidate identifiers; do not store raw visitor content.
- candidate_ids: bounded list of canonical registry identifiers only, maximum four as enforced by the current trace contract.
- delivered_answer_provenance: enum, e.g. provider_composition, deterministic_recovery, registered_recovery, unknown.
- composition_state: bounded enum.
- adjudication_state: bounded enum.
- attempt_count: bounded integer.
- created_at, available_at, claimed_at, lease_expires_at, completed_at, updated_at.
- worker_id: opaque worker instance token, not host identity.
- provider_name and model_name: bounded operational labels, subject to existing redaction rules.
- reason_codes: bounded enum array; no raw provider reasoning or visitor content.
- evidence_refs: bounded canonical evidence/registry references, not copied page text.
- result_version: adjudication contract version.
- last_error_class: sanitized enum; never raw exception text, credentials, or provider payload.

Payload sufficient to adjudicate must be reconstructed from trusted, versioned, privacy-safe source records. If the current system cannot reconstruct the original question/answer and candidate evidence without storing content, the job must be marked not_eligible or insufficient_evidence; do not quietly store raw visitor text to make the workflow convenient. A separate consent/privacy review is required before retaining visitor content.

## 5. Idempotency and lifecycle

Enqueue must be idempotent on (request_id, attempt_ordinal, adjudication_kind). A unique constraint prevents duplicate work for the same request attempt.

Workers claim work transactionally using row locking (FOR UPDATE SKIP LOCKED) and set a bounded lease. Expired leases may be reclaimed. A worker may only complete a job when its claim token/lease is still current. Completion and result insertion must occur in one transaction.

Retry only transient provider/network failures, with a small fixed maximum and exponential backoff plus jitter. Do not retry invalid contracts, missing evidence, policy exclusions, or terminal adjudication decisions.

## 6. Required states

Keep operational inability distinct from a substantive learning decision:

- not_eligible
- queued
- claimed
- budget_skipped
- provider_unavailable
- adjudicated_selected
- adjudicated_rejected
- abstained_insufficient_evidence
- retry_exhausted
- human_review_required

Only adjudicated_selected and adjudicated_rejected represent a completed model judgment. Neither is registry promotion. human_review_required is a workflow gate, not approval.

## 7. Adjudication result contract

A completed result must be structured and schema-validated:

- selected candidate identifiers (subset of supplied candidates);
- rejected candidate identifiers (subset of supplied candidates);
- abstained candidate identifiers (subset of supplied candidates);
- bounded reason codes for each disposition;
- applicability conditions and abstention boundaries, selected from bounded structured fields;
- evidence references supporting the judgment;
- explicit insufficient_evidence indicator;
- adjudicator provider/model/version and timestamp.

The adjudicator must evaluate the actual delivered answer, not merely the provider's discarded draft. It must not infer application from candidate retrieval, prompt exposure, or exact-span presence. Exact-span checks are mechanical evidence only, not semantic proof.

Prefer a provider/model independent from the composer where available. If independence is not available, record the same-provider condition explicitly and lower the evidential strength.

## 8. Provider capacity policy

The current provider quota controller is process-local and explicitly does not provide cross-instance atomic reservations. Do not describe a local counter as a global protected reserve.

A real shared reserve requires one of:
- a shared atomic reservation table/transaction in PostgreSQL, with bounded reservation expiry and operation-class budgets; or
- a genuinely separate upstream provider account/quota allocation.

Reservation admission must be atomic, time-bounded, and observable. A worker must not start a provider call without a valid reservation. Expired reservations are reclaimable. Capacity denial is budget_skipped, not rejection.

The initial policy should be conservative and configurable. Do not hard-code an allocation percentage before measuring actual request volume, token usage, provider failures, and adjudication backlog. Maintain a small exception path for visitor requests where deterministic response quality or safety is inadequate.

## 9. Deadline and execution model

Visitor response delivery must not wait for post-response adjudication. Do not use untracked fire-and-forget tasks.

The durable enqueue operation must be bounded and must not become a new failure dependency for answer delivery. If enqueue fails, deliver the answer and emit a sanitized enqueue-failure event; learning work is recorded as unavailable, not silently claimed as queued.

Worker execution must have bounded concurrency, provider timeout, retry cap, lease duration, and queue-age alert threshold. The worker must be independently restartable and must not compete with the web process's 512 MB memory budget.

## 10. Schema outline

Recommended initial PostgreSQL tables:

### gold_star_adjudication_jobs
One row per idempotent adjudication work item. Includes the opaque IDs, candidate identifiers, provenance, state, attempt count, lease metadata, timestamps, and sanitized error class.

### gold_star_adjudication_results
Append-only result records keyed to job ID and result version. Stores validated dispositions, reason codes, bounded applicability/abstention fields, evidence references, adjudicator identity/version, and completion timestamp.

### provider_capacity_reservations
Atomic shared reservation ledger keyed by reservation UUID. Stores operation class, bounded token estimate, reservation state, expiry, and timestamps. No API keys or provider credentials.

### gold_star_adjudication_events
Append-only state-transition events with opaque job ID, prior/new state, reason code, worker token, and timestamp. No raw question/answer or provider prompt/response.

Use database constraints for state enums, candidate-count bounds, positive attempt counts, unique idempotency keys, foreign keys, and lease invariants. Apply schema changes through versioned migrations and verify rollback strategy before production use.

## 11. Security and operations

- Keep database access private to the Render region/network; do not open PostgreSQL to 0.0.0.0/0.
- Store connection credentials only in Render-managed secret environment variables; never in Git, issue comments, logs, or tool output.
- Use a least-privilege database role for the worker and a separate migration role where feasible.
- Enable encrypted transport and verify TLS behavior.
- Set bounded retention for job metadata and events; document deletion/retention policy.
- Do not store raw prompts, answers, user identifiers, or provider secrets.
- Use connection pooling with a conservative pool size suitable for the 256 MB database plan.
- Monitor database connections, memory, disk, queue age, lease expiry, retries, and worker health.

## 12. Acceptance criteria

1. A deterministic answer can be delivered even when enqueue or provider adjudication is unavailable.
2. Eligible candidate work is durably enqueued and survives web-process restart and deployment.
3. Duplicate enqueue calls produce one job.
4. Two workers cannot simultaneously own the same live lease.
5. Expired leases are recoverable without duplicate result insertion.
6. Provider capacity reservations are atomic across concurrent instances.
7. Budget denial, provider outage, abstention, rejection, and selection are distinct terminal outcomes.
8. Claim adjudication remains separately named and separately measured.
9. No raw visitor question/answer or identity is stored by default.
10. Model adjudication cannot promote a registry item.
11. Held-out paired evaluation is required to demonstrate future response improvement.
12. Production integration is disabled until schema, migration, worker, connectivity, and rollback tests pass.

## 13. Deployment prerequisite

The Render PostgreSQL instance living-archive-adjudication-ledger is provisioned in Gerald's Workspace-primary, Oregon, PostgreSQL 18, basic 256 MB, 1 GB disk. The Render hosted query tool cannot connect while the database IP allowlist is empty. Do not weaken that allowlist. Configure the production service's database reference using Render's private/internal connection mechanism, without exposing the connection string to GitHub or logs.

The existing root render.yaml describes a legacy Singapore mirror service and must not be repurposed as the primary service's deployment definition. Use a separately reviewed deployment integration for the primary service and worker.

No production environment variables, provider quotas, request deadlines, or live routing should change until the above prerequisites are met.
