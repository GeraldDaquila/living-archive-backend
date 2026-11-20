# HRN Composition Contract Guard — live source snapshot (2026-10-18)

**Status: recovery evidence only. Not a deployment package.**

## Provenance

- WordPress path: `plugins/living-archive-hrn-composition-contract-guard/living-archive-hrn-composition-contract-guard.php`
- Live plugin version: **1.3.7**
- Cowboy MCP audit record: **27729**
- Audit timestamp: **2026-10-18 06:52:34** (WordPress/Cowboy displayed time basis)
- Audit result: successful `wp_write_file` call; exact `args.content` preserved in the audit payload
- Recovered UTF-8 byte length: **14,493**
- Live `wp_list_directory` size: **14,493 bytes**
- Live directory modification timestamp: **2026-10-18 06:52:34**
- Snapshot: `living-archive-hrn-composition-contract-guard-v1.3.7.php`

The recovered source was taken from the successful audit payload, not reconstructed from memory or a historical repository copy. Its UTF-8 byte length matches the current live directory inventory and the audit timestamp matches the reported file modification timestamp.

## Important limitations

- Cowboy MCP's `wp_read_file` reports successful calls but currently returns no usable file content for this source path. A byte-for-byte reread of the live file is therefore still unavailable.
- Matching audit payload, byte length, and timestamp are strong provenance evidence, but they are not an independent live readback.
- This snapshot is not proof that HRN's response composition is healthy. Live multi-turn E2E currently fails: later turns return `bounded_contextual_fallback_v9`, lose the journey ledger, and do not advance the reported unit position consistently.
- Do not copy this file back to WordPress, activate it, or use it to replace the live plugin as part of recovery.
- The frozen HRN writer remains out of scope for modification.

## Current finding

The v1.3.7 response-boundary guard adds the `bounded_contextual_fallback_v9` response after upstream composition failure. This fallback preserves a response and question but repeats a generic prompt across turns. The current source snapshot now makes that boundary inspectable; the next repair must preserve the frozen writer and improve or correctly gate the boundary recovery using a reviewed, source-grounded change.

No WordPress source was modified by this snapshot operation.
