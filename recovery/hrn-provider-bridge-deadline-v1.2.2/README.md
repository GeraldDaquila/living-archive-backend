# Provider Bridge Deadline Guard v1.2.2 — reserved mirror/recovery budget

**Candidate only. Not installed on WordPress.**

## Rationale

The live v1.2.1 test confirmed that allowing a recovery call only after the mirror replay is insufficient unless time is reserved for both operations. The mirror used roughly 2.8 seconds of a 4.6-second remaining budget, leaving only 1.82–1.88 seconds for the recovery writer.

## Candidate behavior

- Keep the shared 11.5-second turn deadline and the single mirror-replay limit.
- Cap an HRN relational mirror replay at **2.0 seconds**.
- Permit the mirror replay only when at least **4.4 seconds** remain: 2.0 seconds for the mirror, 2.0 seconds for the recovery writer, and the existing 350ms response buffer.
- If less than 4.4 seconds remain, skip the mirror replay without consuming its budget; preserve the remaining time for the existing recovery writer on Primary.
- Permit one recovery-only primary call when at least **2.35 seconds** remain, capped at **2.0 seconds**, whether or not the mirror replay ran.
- Consume the recovery attempt exactly once. Block further primary calls and any mirror replay after that recovery attempt.
- Continue to require the exact recovery marker in a server-authored system-role message for the exception; visitor/user content cannot spoof it.

## Tests

The PHP runtime test exercises:
- successful mirror replay followed by recovery with 2.6 seconds remaining;
- skipping mirror replay when only 4.0 seconds remain and allowing direct primary recovery;
- refusal when less than 2.35 seconds remain;
- rejection of visitor-role marker spoofing;
- suppression of a second recovery attempt.

The frozen HRN writer, provider quality gates, response-shape requirements, and provider-bank fallback count are unchanged.

## Acceptance gate

Do not install until PHP lint and all CI checks pass. After a full-file replacement through Cowboy MCP, HRN remains NO-GO until a live three-turn WordPress test returns a contextual response and distinct question, preserves `journey_ledger`, advances `unit_position`, and respects the 11.5-second turn deadline.
