# Provider Bridge Deadline Guard v1.2.1 — recovery-only primary call candidate

**Candidate only. Not installed on WordPress. Do not replace the live file until CI and live acceptance gates pass.**

## Evidence

The current live file inventory reports:

- Path: `plugins/la-provider-bridge-deadline/la-provider-bridge-deadline.php`
- Version: **1.2.0**
- Size: **8,582 bytes**
- Modification time: **2026-10-15 09:41:01**

The recovered v1.2.0 snapshot at `recovery/wordpress-live-2026-10-16/la-provider-bridge-deadline.php` is 8,580 characters / 8,582 UTF-8 bytes and matches the live inventory size and modification record. Direct byte-for-byte readback is still unavailable through the current Cowboy MCP file reader, so exact identity is strongly indicated but not independently verified.

## Live defect

The v1.2.0 guard allows one bounded mirror replay for `hrn_relational`, then blocks every further primary call for the rest of the WordPress request. The HRN v0.5.332 writer has an existing server-authored recovery-writer path that calls the same provider bridge after the initial composition cannot be used. The guard suppresses that recovery request as “whole-turn mirror replay already consumed,” leaving the response boundary to return a generic fallback.

## Candidate change

- Keep the 11.5-second shared visitor-turn deadline and existing one-mirror-replay rule.
- Permit **one** additional primary call only when its system-role message contains the trusted, server-authored HRN recovery-writer marker and the operation is `hrn_relational`.
- Cap this recovery-only request at 2.5 seconds and require at least 2.85 seconds of remaining turn budget, preserving the existing 350ms response buffer.
- Refuse the exception if the marker appears only in visitor/user content, if the turn budget is too low, or if a recovery attempt has already been consumed.
- Do not change the frozen HRN writer, provider quality gates, response-shape checks, fallback count, or provider timeouts.

## Acceptance

CI must pass the PHP syntax and runtime guard tests. After a reviewed full-file replacement via Cowboy MCP, live multi-turn E2E must show:
- a non-generic, visitor-grounded response on turns 2 and 3;
- a distinct, grounded follow-up question;
- `journey_ledger` present and consistent;
- `unit_position` advancing;
- no second mirror replay or deadline overrun.

Until then HRN remains **NO-GO**. This candidate has not modified the live WordPress file.
