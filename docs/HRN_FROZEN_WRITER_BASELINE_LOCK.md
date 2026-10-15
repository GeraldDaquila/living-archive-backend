# Human Relational Navigator — Frozen Writer Baseline

**Status:** FROZEN REFERENCE — NOT A DEPLOYMENT CANDIDATE  
**User-designated baseline:** HRN v0.5.129 archive  
**Preserved on:** 2026-10-15  
**Purpose:** Preserve the last HRN writer copy supplied by the steward, independently of later WordPress-only iterations.

## Immutable artifacts

The exact user-supplied archive and extracted writer are preserved in the steward's ChatGPT Library as:
- `HRN-v0.5.129-observer-stop-boundary-latency-RELEASE(2).zip`
- `HRN-Frozen-Writer-Baseline-v0.5.129.zip`
- `HRN-Frozen-Writer-v0.5.129.php`
- `HRN-Frozen-Writer-v0.5.129-MANIFEST.txt`

Integrity values:
- Original archive SHA-256: `5c427fbce98858444cb80289ad20cc41023b1efc516cd02f57458beb52a36d83`
- Frozen writer SHA-256: `6253e47fd66be5df40664c2a1be35a223e7e0057f841f42abe3808ea1c616fda`
- Writer size: 361,552 bytes
- Static PHP syntax check: PASS

## Version identity caveat

The archive name and runtime version constant claim v0.5.129, but the PHP plugin header says v0.5.127. This discrepancy is preserved exactly. The archive's own QA report says the release was **NOT YET LIVE** and requires manual activation and fresh live E2E.

Static review also found a STOP/junction control-flow inconsistency in this saved copy: the code sets the junction flag after Observer STOP and later resets it before the landing decision. Do not describe this artifact as a proven working production release or blindly install it over live v0.5.330.

## Protection rules

1. Treat the preserved writer and original archive as immutable historical references.
2. Never overwrite these artifacts with a later iteration.
3. Develop any repair in a separately versioned candidate, with source provenance and explicit diffs.
4. Do not modify the frozen General Purpose USE gold-standard fixture or protected `use_core.py` while working on HRN.
5. Do not deploy this writer merely to restore a version number. A replacement requires PHP syntax checks, HRN voice/safety/grounding regressions, visitor-equivalent E2E, and verification of the USE return path.
6. Do not claim byte identity to WordPress HRN v0.5.330 or any prior live version. That identity has not been established.

## Relationship to current production

The live WordPress HRN was observed at v0.5.330 and fails some relational turns with `missing_question` / `composition_unavailable`. The exact live v0.5.330 source has not yet been recovered through a supported, auditable export. The repository's tracked writer is v0.5.326 and is not byte-identical to the live file.

This lock preserves the steward's chosen reference; it does not declare production recovered. Overall release status remains NO-GO until the live HRN visitor journey is restored and verified.
