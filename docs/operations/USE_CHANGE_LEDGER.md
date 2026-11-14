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


## 2026-11-14 — Technical capability and legitimate authority Gold Star

- **Class:** Content / QA authority
- **Intent:** Replace generic abstention behavior for the exact conceptual relationship with a direct, bounded distinction.
- **Canonical benchmark:** `gs-2026-11-14-technical-capability-legitimate-authority`.
- **Structural discipline:** Separate capability from the right to exercise power; examine mandate, accountability, safeguards, affected interests, and correction.
- **Gold Star authority:** Exact-answer authority and active quality contribution approved; doorway retained as canonical continuation.
- **Regression boundary:** Do not let generic uncertainty displace a conceptual distinction that can be answered directly, and do not treat expertise or technical success as self-validating authority.

## 2026-11-14 — Full Gold Star runtime activation

- **Class:** Content / QA authority
- **Intent:** Make every user-approved Gold Star available to the Guide's relevance-selected qualitative learning layer.
- **Canonical contracts:** `docs/qa/gold_standard_registry.json`, `docs/qa/gold_star_qualitative_transfer_review.json`, and `scripts/validate_gold_star_registry.py`.
- **Decision:** Availability is universal across user-approved Gold Stars; relevance and abstention boundaries determine influence on any individual answer.
- **Validation boundary:** Every approved Gold Star must be runtime-active and have qualitative-transfer coverage; registry and review IDs must remain unique.
- **Rollback point:** Parent canonical commit before this PR merge.
