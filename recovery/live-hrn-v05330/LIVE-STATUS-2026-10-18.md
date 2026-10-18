# HRN live status reconciliation — 2026-10-18

**Status: source identity is strongly indicated but not byte-for-byte verified. Do not deploy, overwrite, roll back, or activate any candidate from this note.**

## Current WordPress inventory

Cowboy MCP read-only checks reported:

- Active plugin: `plugins/human-relational-navigator/human-relational-navigator.php`
- Plugin inventory version: **0.5.332**
- Current file size: **546,114 bytes**
- Current file modification time: **2026-10-16 17:12:50**

The current v0.5.332 candidate tracked in this recovery branch has the same version and an independently calculated UTF-8 size of **546,114 bytes**.

The WordPress change journal also records a file update at **2026-10-16 17:12:50** for this exact path. Its captured before-state is **537,027 bytes**, matching the recovered v0.5.330 source size. This is consistent with the v0.5.332 candidate replacing v0.5.330 on the live site.

## What this establishes—and what it does not

The evidence strongly suggests the current active WordPress file may be the v0.5.332 candidate. It does **not** prove byte-for-byte identity: Cowboy MCP's `wp_read_file` records successful calls but returns no usable file content, and the change journal does not expose the full after-state bytes.

The earlier PR description that characterized v0.5.332 as not deployed is therefore no longer a safe assumption. Use the current live inventory and change journal as the latest evidence, while preserving the caveat that exact bytes are not verified.

## Correlated live E2E finding

A controlled three-turn WordPress test on 2026-10-18 returned HTTP 200 each time, but turns 2 and 3 used `bounded_contextual_fallback_v9` from composition guard v1.3.7. Both turns repeated the same generic response and question, omitted `journey_ledger`, and did not advance `unit_position` consistently.

Render logs during the same test window show:
- Groq relational drafts rejected for short response shape (under two complete sentences / 180 characters).
- Groq relational drafts rejected for visitor-surface `action-guidance`.
- OpenRouter rate limits, Groq TPM-budget exhaustion, and Workers AI timeouts.
- Some provider-bank calls returned structurally valid response/question keys, so the remaining boundary between provider-bank acceptance and HRN's downstream composition acceptance still requires request-correlated tracing.

The source snapshot of composition guard v1.3.7 is preserved separately under `recovery/wordpress-live-2026-10-18/`. It confirms the generic fallback is added at the REST response boundary, not by a string in the HRN writer.

## Safety decision

- HRN remains **NO-GO** for visitor acceptance.
- Keep the frozen writer unchanged.
- Do not weaken the humanity or visitor-surface gates to make a provider response pass.
- Do not deploy a new guard or HRN candidate until provider-bank vs. HRN validation is traced with correlated request identifiers and multi-turn ledger continuity is restored.
