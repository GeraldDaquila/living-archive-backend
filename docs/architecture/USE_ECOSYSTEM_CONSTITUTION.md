# USE Ecosystem Constitution

**Status:** Canonical operational contract  
**Authority:** Living Archive USE ecosystem  
**Purpose:** Make the production environment self-describing so no operator or assistant must rely on conversational memory to change it safely.

## 1. Canonical authority
- Production repository: `GeraldDaquila/living-archive-backend`.
- Canonical production branch: `main`.
- Production application entrypoint: `main.py`.
- Test application entrypoint: `test-main.py`.
- Cowboy MCP is the sole WordPress/site administration authority.

## 2. Two-server production contract
- USE Primary and USE2-Mirror must run the same approved production identity and canonical source revision before a coordinated release is declared stable.
- Primary/Mirror routing policy is 70/30 unless an explicitly approved incident procedure changes it.
- A server health observation is not sufficient to declare release stability; deployment state, identity, health and release gates must agree.

## 3. Retrieval and fallback contract
- Pinecone remains 384-dimensional.
- The canonical embedding architecture remains BAAI/bge-small-en-v1.5 unless explicitly changed through a constitutional review.
- When Pinecone is unavailable or budget-constrained, the canonical asset/meta-crosslink fallback is used; temporary degradation must not silently create a second retrieval authority.
- Quality takes precedence over latency when provider selection requires a tradeoff.

## 4. Gold Star authority
- Sole canonical ledger: `docs/qa/gold_standard_registry.json`.
- Sole canonical qualitative-transfer governance: `docs/qa/gold_star_qualitative_transfer_review.json`.
- Runtime consumer: `gold_star_lessons.py`.
- Historical repositories or mirrors are evidence-only unless explicitly promoted through a documented migration.
- Canonical storage does not imply runtime learning. Only records explicitly approved for runtime transfer may contribute.
- Registry integrity must be validated before merge; production startup is the final guard, never the first schema test.

## 5. Mandatory change protocol
Before changing production-affecting material:

1. Read this Constitution and `docs/operations/USE_ECOSYSTEM_STATE.md`.
2. Inspect the current canonical implementation and affected contracts.
3. Classify blast radius: content, runtime, infrastructure, or constitutional.
4. Run all applicable validation before merge.
5. Merge only one coherent, validated change set.
6. Verify both servers against the same release identity.
7. Record the resulting state in the operational state manifest.

Direct production commits may not be used to discover missing schema fields.

## 6. Stop conditions
Stop and investigate rather than patch repeatedly when:
- a deployment exposes a contract that was not validated beforehand;
- Primary and Mirror disagree on release identity;
- a canonical registry has competing sources of authority;
- more than one corrective production commit is required for the same schema defect.

## 7. External-memory principle
Repository contracts, manifests, tests and health evidence are the source of operational truth. Conversational memory is advisory context only and is never sufficient authority for production changes.
