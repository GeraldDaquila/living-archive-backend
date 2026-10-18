# Cowboy MCP WordPress source recovery snapshot — 2026-10-16

**Status: recovery evidence only; not a deployable WordPress plugin package.**

This directory preserves the latest successful Cowboy MCP `wp_write_file` payloads for three active response-boundary components. It does not contain the live Human Relational Navigator entrypoint itself. The live-file reader returned empty payloads even for small text files, so the source bytes were recovered from Cowboy MCP's audit records.

For each component, the captured payload's UTF-8 byte length exactly matches the live WordPress directory inventory's reported file size and modification timestamp. This is strong consistency evidence, but because the direct reader failed, byte-for-byte live reread verification remains unavailable.

| Snapshot file | Original wp-content path | Cowboy audit record | Audit timestamp | UTF-8 bytes | Git blob SHA-1 |
|---|---|---:|---|---:|---|
| `recovery/wordpress-live-2026-10-16/living-archive-hrn-composition-contract-guard.php` | `plugins/living-archive-hrn-composition-contract-guard/living-archive-hrn-composition-contract-guard.php` | 20668 | 2026-10-15 10:24:09 | 12253 | `909fee9108795254db3c2aa29aaa1deedd5988e7` |
| `recovery/wordpress-live-2026-10-16/hrn-command-boundary-adapter.php` | `plugins/hrn-command-boundary-adapter/hrn-command-boundary-adapter.php` | 17626 | 2026-10-14 04:04:58 | 17966 | `dd100725f7560bfbbc8e2d530adb64a87e75cbbd` |
| `recovery/wordpress-live-2026-10-16/la-provider-bridge-deadline.php` | `plugins/la-provider-bridge-deadline/la-provider-bridge-deadline.php` | 20509 | 2026-10-15 09:41:01 | 8582 | `9deefc5674ed167ab608bd6dbc7f5da818322eb2` |

## Handling rules

- Do not copy these files back to WordPress from this recovery directory.
- Do not treat this snapshot as a release or as proof that HRN's live writer is healthy.
- The live HRN entrypoint `plugins/human-relational-navigator/human-relational-navigator.php` (v0.5.330, recorded size 537,027 bytes) remains unrecovered byte-for-byte.
- Preserve the frozen writer and current production components until exact-source comparison and full visitor E2E tests are complete.
- Git blob SHA-1 values fingerprint the recovered snapshot blobs; they are not SHA-256 file digests.
