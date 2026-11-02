# Relational Return Authentication — Candidate Acceptance

Status: isolated candidate only. This document does not authorize production rollout.

## Contract

- The WordPress Command Boundary Adapter is the server-side caller.
- USE requires HMAC-SHA256 over the exact request bytes:
  `timestamp + LF + nonce + LF + raw_body`.
- Required headers: `X-LA-Relational-Timestamp`, `X-LA-Relational-Nonce`, and `X-LA-Relational-Signature`.
- Timestamp window: 300 seconds.
- Nonce: 16–128 URL-safe characters; the WordPress adapter currently emits 128-bit random hex.
- Signature comparison is constant-time.
- USE rejects missing/short secrets, malformed signatures, expired timestamps, replayed nonces, and a saturated replay cache.
- Secret name on both sides: `LA_RELATIONAL_RETURN_SHARED_SECRET`.
- WordPress secret must be a server-side `wp-config.php` constant. Render secret must be a private environment variable. Never expose either to browser configuration.

## Rollout sequence — not yet authorized

1. Generate a new high-entropy secret outside source control. Never place its value in GitHub, logs, chat, or a frontend option.
2. Configure the same secret in a non-production WordPress test environment and isolated USE test service.
3. Run authenticated success, missing-secret, missing-header, bad-signature, expired-timestamp, replay, malformed-body, and oversized-body tests.
4. Verify the exact PHP/Python canonical byte string against shared test vectors.
5. Verify WordPress adapter response handling and primary/mirror behavior.
6. Remove the browser-side direct relational-return call only after confirming the server-side adapter is the sole authoritative caller and browser continuity tests pass.
7. Deploy both sides in a coordinated window with a verified rollback pair. Do not enable this USE gate on production before WordPress has the matching secret and signed caller, or all legitimate handoffs will fail closed.

## Explicit limitations

- The nonce cache is process-local. It blocks replay on the same running instance but is not a durable cross-instance idempotency ledger.
- Primary and mirror have independent nonce caches. Replaying the same signed request to the mirror can therefore be accepted independently.
- This candidate does not yet establish exactly-once delivery or durable session-level idempotency.
- The existing WordPress browser-side handoff must be removed/disabled separately after its installed source is safely inspected.
- The current production WordPress and Render environments have not been changed.
