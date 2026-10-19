# Provider Bridge Deadline Guard v1.2.1 — live deployment record

**Live status: installed on WordPress; acceptance failed. HRN remains NO-GO.**

## Provenance

- WordPress path: `plugins/la-provider-bridge-deadline/la-provider-bridge-deadline.php`
- Version: **1.2.1**
- Installed through Cowboy MCP with a full-file replacement on **2026-10-18 13:32:34 UTC**
- WordPress change journal ID: **7168**
- Live file size after write: **11,885 bytes**
- Source candidate: this branch's `la-provider-bridge-deadline.php` (11,881 characters / 11,885 UTF-8 bytes)
- Prior version: v1.2.0, recovered from the successful source-write audit payload and matching live inventory size/time

## What v1.2.1 changed

It allowed one server-authored HRN recovery-only primary call after the single mirror replay, provided at least 2.85 seconds remained, and capped that call at 2.5 seconds. The frozen HRN writer, 11.5-second shared deadline, and response-quality gates were not changed.

## Live E2E result — FAIL

A fresh three-turn WordPress test returned HTTP 200 on all turns, but turns 2 and 3 still used the generic `bounded_contextual_fallback_v9` from composition guard v1.3.7, omitted `journey_ledger`, and did not preserve/advance the reported unit position.

The PHP log showed the exact reason the new allowance did not activate:

- Primary failure left about **4.6 seconds**.
- The guard allowed the mirror replay, which used about **2.8 seconds**.
- The subsequent recovery call was correctly refused because only **1.82–1.88 seconds** remained, below the 2.85-second requirement.

This version is retained as the deployed, tested intermediate state. Do not revert it solely because acceptance failed; v1.2.2 is intended to fix the budget allocation without changing the writer.

## Next candidate

See `recovery/hrn-provider-bridge-deadline-v1.2.2/README.md`. Version 1.2.2 reserves two seconds for the mirror and two seconds for the recovery writer, plus the existing 350ms response buffer. When there is insufficient time for both, it skips the mirror replay and preserves time for direct recovery on Primary.

No frozen HRN writer changes were made.
