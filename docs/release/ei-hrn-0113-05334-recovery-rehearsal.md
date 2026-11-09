# EI 0.1.3 / HRN 0.5.334 production recovery rehearsal

Status: **preflight blocked; production unchanged**  
Candidate PR: [#1107](https://github.com/GeraldDaquila/living-archive-backend/pull/1107)  
Candidate commit: `d2b51824ece6746d1123bbdef66d2f2e25641547`

## Verified live baseline (2026-11-09)

| Component | Live state |
|---|---|
| Human Relational Navigator | `0.5.333`, active |
| Living Archive Emergency Intelligence | `0.1.2`, active |
| EI registry schema | `0.1` |
| EI registry version | `2026.10.13.001` |
| EI registry `signature_required` | `false` |
| EI status/resolve routes | Present |
| Candidate resolve-bundle / HRN emergency-resources routes | Not present |

The live plugin file sizes and modification times were read through Cowboy MCP. The current EI directory includes the registry, resolver, selector, engine, API, admin, updater, presenter, and tests.

## Blocking recovery finding

The installed temporary plugin `hrn-rollback-capture` is not version-neutral. Its source hard-codes:

- expected source version: `0.5.310`
- backup filename: `human-relational-navigator-v0.5.310-20261013.php`

The live HRN is `0.5.333`. The helper therefore refuses to capture the current HRN file and is not an acceptable rollback mechanism for this release.

The existing Cowboy database checkpoint facility is database-only. It does not replace byte-exact backups of the HRN and EI plugin trees or the EI registry.

## Required recovery artifact

Before deployment, create and verify one private, immutable release snapshot containing:

1. The complete live HRN plugin directory.
2. The complete live EI plugin directory, including `data/emergency-registry.json`.
3. A manifest containing every relative path, byte size, and SHA-256 digest.
4. The live plugin versions, registry schema/version, and capture timestamp (UTC).
5. A verified archive checksum and a second verification pass after archive creation.

The snapshot must be stored outside the public web root or protected by server-level deny rules. The manifest must not contain API keys, secrets, visitor data, or database dumps.

A snapshot is accepted only if every manifest entry matches the captured bytes, no required file is missing, no unmanifested plugin file is present, and the archive can be reopened and re-hashed. Keep the archive and manifest read-only for the duration of the release.

## Deployment order (not authorized yet)

1. Capture and independently verify the recovery artifact.
2. Create a fresh database checkpoint labelled for the EI/HRN release.
3. Install EI `0.1.3` first; preserve active state.
4. Verify `LAEI_VERSION=0.1.3`, registry schema `0.2`, registry version `2026.11.09.001`, required provenance fields, and the expected REST routes.
5. Confirm remote registry updates remain disabled until trusted-key signature verification exists.
6. Install HRN `0.5.334` second; preserve active state.
7. Verify the minimum-version guard and shared EI-only resource resolver.
8. Run smoke tests for: current verified Philippines resource; expired verification; missing provenance; unverified record; unsupported country; EI unavailable/malformed response; and explicit-country confirmation.
9. Confirm no legacy HRN number is emitted in any failure case and no visitor answer/transcript crosses into EI.
10. Re-read plugin versions, routes, registry state, and site health.

## Rollback requirements

- Restore the exact EI and HRN plugin trees from the captured artifact, not from guessed historical versions.
- Restore the EI registry from the same artifact.
- Verify restored file sizes and SHA-256 hashes against the original manifest.
- Verify the old route/version baseline and perform site-health checks.
- Do not restore the entire database checkpoint merely to roll back plugin files. A database restore can discard unrelated content created after the checkpoint; use it only if a separately identified database mutation requires it and after reviewing that data-loss consequence.

## Go / no-go gate

**No-go** until all of the following are evidenced:

- Complete, byte-exact snapshot exists.
- Archive integrity and manifest verification pass twice.
- Restoration has been rehearsed against a disposable copy or isolated test WordPress instance.
- EI-first / HRN-second deployment package identities are pinned.
- Smoke tests and rollback checks are executable and documented.

PR #1107 remains draft and unmerged. This document does not authorize merge, production file writes, activation/deactivation, registry changes, or deployment.
