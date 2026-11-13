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
