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


## 2026-11-14 — Organizational learning Gold Star live calibration confirmation

- **Class:** Content / runtime acceptance evidence (no canonical response change)
- **Intent:** Confirm the user-approved Gold Star exemplar for “How do organizations create conditions for learning from failure?” remains a successful live calibration response after the canonical doorway repair.
- **Canonical contract:** Existing immutable Gold Star record `gs-2026-11-14-organizational-learning-from-failure`; no duplicate record created and no canonical prose changed.
- **Validation:** Live visitor screenshot confirmed the answer and required canonical continuation render together at the visitor boundary.
- **Result:** PASS — retain as active Gold Star and canonical acceptance reference.
- **Release relationship:** Confirms the doorway protection introduced by merge commit `38b6a0a21fa21a0793c4bb00fb1b17226418cdef`.
