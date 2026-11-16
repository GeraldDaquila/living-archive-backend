# USE Ecosystem State Manifest

**Purpose:** Current-state handoff and release record. Update only after verified state changes.

## Canonical identity
- Repository: `GeraldDaquila/living-archive-backend`
- Production branch: `main`
- Production entrypoint: `main.py`
- Test entrypoint: `test-main.py`

## Current release record
- Canonical commit: **a67500ab6c5645f467082940ccf8e73954a058ed** — merged PR #1529, 2026-11-16.
- Build/version/fingerprint: **v489.311** / `USE-v489.311-source-derived`.
- Primary deployment state: **LIVE** on canonical commit `a67500ab6c5645f467082940ccf8e73954a058ed` (Render service `srv-da98sm2jnfac73d2ki5g`, deployment `dep-dbt6iok9v7es73clgr7g`).
- USE2-Mirror deployment state: **LIVE** on the same canonical commit `a67500ab6c5645f467082940ccf8e73954a058ed` (Render service `srv-db2s2bid0e5s73e7gt9g`, deployment `dep-dbt6iok9v7es73clgqrg`).
- Last coordinated release gate: **PASS** — both servers report the same commit and live deployment; candidate TEST exact-answer/no-doorway and positive-doorway controls passed; seven candidate CI workflows passed. Verified 2026-11-16 10:26 +08.
- Temporary provider condition: Pinecone unavailable during candidate verification; configured fallback active. Provider-lane and broader two-server acceptance beyond matching deployment identity are not claimed here.

## Active architecture
- Two-server topology: Primary + USE2-Mirror
- Routing policy: 70/30
- Pinecone: 384-dimensional canonical architecture
- Gold Star canonical ledger: `docs/qa/gold_standard_registry.json`
- Gold Star transfer governance: `docs/qa/gold_star_qualitative_transfer_review.json`
- Gold Star runtime consumer: `gold_star_lessons.py`

## Temporary constraints / incidents
Record only active constraints here. Remove or close entries when the condition is resolved.

## Handoff rule
Any operator beginning production work must read this manifest and the USE Ecosystem Constitution before making a production-affecting change.
