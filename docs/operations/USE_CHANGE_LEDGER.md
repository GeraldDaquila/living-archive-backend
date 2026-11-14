# USE Change Ledger

Every production-affecting change must be classified before merge.

| Class | Examples | Minimum gate |
|---|---|---|
| Content | Copy, canonical response, Gold Star prose | Relevant schema/integrity validation |
| Runtime | Python routing, provider logic, learning engine | Test environment + regression checks |
| Infrastructure | Render, deployment, environment variables | Two-server coordinated verification |
| Constitutional | Authority, canonical location, architecture | Explicit approval + full ecosystem audit |

## Required release record
For each release, record:
- intent and blast-radius class;
- affected canonical contracts;
- validation performed and result;
- canonical commit;
- Primary and Mirror release identity;
- rollback point;
- final gate result.

**Rule:** Production deployment logs may confirm a release; they may not be used as the primary mechanism for discovering incomplete schemas.


## 2026-11-14 — Sacred-language Gold Star live acceptance

- **Class:** Content / QA authority
- **Intent:** Record completed live acceptance of the canonical sacred-language Gold Star response package.
- **Affected contract:** `gs-2026-11-14-sacred-language-clarity-power-live-candidate`; exact response plus canonical doorway.
- **Validation:** Direct visitor-side review confirmed the approved response and visible rendering of **The Power of Language & Symbol** doorway.
- **Authority decision:** Retain the existing canonical Gold Star; do not create a duplicate benchmark. Mark doorway status `LIVE_RENDER_VALIDATED`.
- **Transfer boundary:** `runtime_transfer` remains unchanged; live acceptance of an exact benchmark does not by itself authorize cross-question transfer.
- **Rollback point:** Parent commit before this content-authority update.
- **Final gate:** Canonical record updated and committed on protected release branch; merge remains subject to normal review.
