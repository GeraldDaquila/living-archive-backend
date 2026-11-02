# Shared Provider Health Contract Repair — Acceptance Specification

Status: TEST-only candidate rebuild. Production remains frozen.
Baseline: `main` at `b85c0c5981e0b1a5f8fe79c47b97ba9582f4941e` (USE v489.309).
Branch: `test/provider-health-v2-v489309`.
Preserve all v489.309 production changes, including the five-candidate General Guide fallback policy and 18-second arbitration window.

## Scope

Repair only the shared Provider Bank health-state persistence seam between the USE primary, mirror, and the authenticated WordPress database bridge. Do not change provider selection policy, inference budgets, visitor-facing composition, HRN validators, or specialist contracts.

## Invariants to preserve

- Shared health remains advisory; process-local circuit state remains authoritative when the bridge is unavailable.
- Preserve the production 250ms HTTP timeout, 2-second read cache, cold-read single-flight, and 5-second bridge circuit breaker.
- Preserve route-level batching: one coherent health snapshot per inference route, not one write per failed candidate.
- Preserve timestamp-based transport and quality merge semantics.
- Never persist prompts, visitor content, model outputs, credentials, or probe ownership.
- Never block inference on a global provider-state lock or unbounded persistence retry.
- Do not change the active WordPress plugin, production Render services, production `main`, or any live database during TEST development.

## Required implementation

### WordPress endpoint

1. Require an explicit supported contract version on POST.
2. Validate the entire batch before performing any write: object shape, maximum 100 entries, key syntax/length, record types, and field types/ranges.
3. Reject the entire batch on any invalid record; do not silently skip records.
4. Check JSON serialization before database writes.
5. Use an InnoDB transaction for the complete batch. A read/merge/write failure must roll back every record.
6. Return a success indicator, contract version, submitted count, and committed count. Success is true only when every submitted record is committed.
7. Keep GET deterministic and bounded. Define an explicit stable capacity policy rather than relying on unordered LIMIT 100.
8. Move schema creation out of ordinary GET/POST request handling; use a controlled activation/upgrade path.
9. Do not change authentication behavior in this repair. Credential externalization/rotation is a separate coordinated security change.

### Python health-store client

1. Require the expected contract version, explicit success indicator, and exact committed count equal to submitted count.
2. Reject booleans as counts even though Python treats bool as int.
3. Reject malformed, partial, zero-write, or wrong-version acknowledgements.
4. Preserve the existing 250ms timeout and read-side cache/circuit behavior.
5. Export the 100 most recently active states using the newest transport/quality event timestamp, with a stable key tie-breaker; do not truncate by dictionary insertion order.
6. Do not report failed writes as successful.

### Provider Bank lifecycle and concurrency

1. Keep route-level batching.
2. Retain a pending/dirty marker when a flush fails.
3. Clear pending state only after a complete acknowledgement for the snapshot version being flushed.
4. If state changes during a flush, the newer version must remain pending.
5. Protect shared mutable provider/quality state, provider cursors, model cursors, and half-open probe ownership with a narrowly scoped state lock.
6. Copy a consistent snapshot under the lock; perform HTTP I/O outside the lock.
7. Do not hold the lock during provider inference or WordPress network I/O.
8. Preserve process-local fallback and do not introduce a volatile unbounded retry queue.

### Cross-language state contract

- Agree on field whitelist, normalization, timestamps, equal-timestamp handling, counters, cooldowns, and expired-cooldown state.
- Preserve `last_operation` because timeout cooldowns are operation-specific.
- `probe_successes` is diagnostic-only: it is exposed in local diagnostics but does not affect provider admission, ranking, cooldowns, or circuit transitions. It is intentionally not persisted across processes.
- Do not persist `probe_in_flight`; always restore it as false.
- Use the same deterministic fixtures against Python and PHP merge implementations.

## Required tests

### WordPress transaction tests
- Valid multi-record batch commits completely.
- Invalid version, malformed record, invalid key, and >100 entries reject before any write.
- Invalid input and input-serialization failures reject before any write; merged-record serialization failure rolls back any reserved placeholders and commits no provider state.
- Simulated failure on a middle write rolls back all changes.
- Two simultaneous writes to the same previously absent key both receive complete acknowledgements; the final row retains the newer timestamp and operation context.
- GET ordering/capacity is deterministic.

### Python acknowledgement tests
- Exact full acknowledgement succeeds.
- Zero, partial, missing, malformed, wrong-version, and false-success acknowledgements fail.
- Boolean count is rejected.
- Failed flush retains pending state.
- A later successful flush clears only the matching snapshot version.

### Concurrency tests
Use deterministic barriers, not timing-only sleeps:
- Same-model success versus failure.
- Provider-wide quarantine versus sibling success.
- Quality rejection versus validated success.
- Remote merge versus local mutation.
- Concurrent snapshots and a newer mutation during an older flush.
- Exactly one half-open probe owner.

### Parity tests
Run identical transport and quality merge fixtures through Python and PHP for:
- Newer success, newer failure, equal timestamps, and stale snapshots.
- Equal failure timestamp counter reconciliation.
- Expired and unexpired cooldowns.
- Operation-specific timeout state.
- Independent quality success/failure ordering.

### Regression and performance
- Existing provider-bank and provider-health tests pass.
- HRN and General Guide regression suites pass unchanged.
- The 250ms shared-store deadline, 2-second read cache, single-flight behavior, and 5-second circuit breaker remain intact.
- No new provider inference calls, retries, or changes to visitor-facing response contracts.

## Release gate

No merge, deployment, WordPress mutation, credential rotation, or production database change until:
1. Complete-unit source audit passes.
2. All targeted and existing regression tests pass.
3. Primary and mirror TEST runtime report the same candidate identity.
4. WordPress TEST bridge transaction and acknowledgement tests pass.
5. Repeated cross-service read/write/restart tests pass.
6. Latency and inference-budget regressions are ruled out.

A green CI run alone is not production acceptance.


## TEST candidate implementation status — 2026-11-01

### Python runtime candidate
- provider_health_store.py speaks contract v2 and rejects wrong-version reads and incomplete writes.
- provider_bank.py retains failed writes as one versioned pending marker, retries at route boundaries, and avoids waiting behind another in-flight persistence call.
- Health transitions, candidate selection/cursors, shared-state merge, snapshot creation, and half-open probe ownership use a narrow state lock.
- Remote provider inventory discovery runs before acquiring that lock; stale candidate snapshots are rechecked for transport and quality cooldowns before a probe or provider call.
- Snapshot serialization occurs under the state lock; HTTP persistence occurs outside it.
- A visitor-contract rejection releases a half-open transport probe claim.

### WordPress bridge candidate
- QA/provider_health_bridge_v2_candidate.php is an isolated, non-loaded candidate; it is not installed on the active WordPress site.
- POST requires v2, validates the entire bounded batch and pre-serializes incoming records before opening the transaction; it then reserves keys, locks/merges/serializes the latest rows, and commits the full write set in one InnoDB transaction. A merge/serialization failure rolls back all reserved placeholders.
- The write path is set-based: one multi-row `INSERT IGNORE` reserves/materializes all bounded keys, one indexed `SELECT ... WHERE state_key IN (...) FOR UPDATE` locks the rows, and one multi-row `INSERT ... ON DUPLICATE KEY UPDATE` commits merged payloads.
- Key reservation occurs inside the same InnoDB transaction. The batch is sorted by state key, then one `INSERT IGNORE` serializes concurrent first-time writes to the same previously absent key before the locking read, avoiding competing gap-lock-to-insert races and reducing deadlocks for overlapping multi-key batches. Placeholder rows are replaced before commit and disappear on rollback.
- Including transaction boundaries, the database statement count is constant (START, key reservation, SELECT, UPSERT, COMMIT), not O(N) per-record reads and writes.
- The PHP harness asserts the same one-reservation/one-read/one-upsert query count for both 2-record and maximum 100-record batches. This guards query complexity but does not substitute for measured latency on the actual WordPress database.
- Any read, serialization, write, or commit failure rolls back and returns no success acknowledgement.
- GET returns v2, retains the 100 most recently updated records with a deterministic key tie-breaker, and does not create or alter schema.
- The existing authenticated permission callback is preserved by the route-registration candidate.
- Schema creation is isolated in an activation-only function; the existing production table is already InnoDB and unchanged.

### Shared parity and test evidence
- QA/provider_health_merge_fixtures_v2.json is consumed by both Python and PHP tests.
- QA/test_provider_health_bridge_v2.php exercises validation, exact acknowledgement, transaction rollback, serialization failures, deterministic GET capacity, and shared merge fixtures.
- The dedicated PHP workflow passed PHP 8.3 and 8.4 syntax checks, the WordPress bridge contract harness, real WordPress 7.1.4 REST integration, 100-record MariaDB batch, transaction rollback, concurrent first-write merge, and the three-process Python client round-trip under both PHP 8.3 and 8.4.
- A real parallel REST test exposed a first-write gap-lock race. The candidate now sorts keys and reserves them with an in-transaction multi-row `INSERT IGNORE` before `SELECT ... FOR UPDATE`. PHP 8.3 and 8.4 CI both passed two simultaneous first-write requests and verified that the final record retained the newer failure timestamp, operation, and consecutive-failure count.
- The provider-health/pathway Python regression workflow passed (27 tests).
- The expanded provider-health batching suite passed: 27 tests. The complete v487 ecosystem validation workflow subsequently completed successfully.

### Remaining release gates
- Complete the full v487 ecosystem regression workflow.
- Perform the full Python unit suite and complete-unit source audit against the latest PR head.
- Integrate the candidate into a genuine isolated WordPress TEST environment and validate real wpdb transaction behavior.
- Verify the same candidate identity on primary and mirror TEST runtimes, then run repeated cross-service read/write/restart and latency tests.
- Do not merge, deploy, mutate active WordPress, or touch production DB until the TEST environment and all acceptance gates are satisfied.
