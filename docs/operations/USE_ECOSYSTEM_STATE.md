# USE Ecosystem State Manifest

**Purpose:** Current-state handoff and release record. Update only after verified state changes.

## Canonical identity
- Repository: `GeraldDaquila/living-archive-backend`
- Production branch: `main`
- Production entrypoint: `main.py`
- Test entrypoint: `test-main.py`

## Current release record
- Canonical commit: **record after coordinated verification**
- Build/version/fingerprint: **record after coordinated verification**
- Primary deployment state: **record after coordinated verification**
- USE2-Mirror deployment state: **record after coordinated verification**
- Last coordinated release gate: **record result and timestamp**

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
