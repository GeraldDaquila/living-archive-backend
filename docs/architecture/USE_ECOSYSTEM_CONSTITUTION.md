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
- There is exactly one canonical approved Gold Star inventory: records with status `USER_APPROVED_GOLD_STANDARD`. Fixture or provenance incompleteness is evidence metadata, not a second approved directory, ledger, or competing count.
- No new parallel approved-status bucket may be introduced without an explicit constitutional amendment and migration of the canonical inventory.

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


### 4.0 Explicit user-review elevation gate

**No candidate may be elevated to `USER_APPROVED_GOLD_STANDARD` unless the user has first reviewed the actual visitor-facing response and explicitly authorized its Gold Star elevation.**

- A rating, assistant recommendation, source recovery, test result, or instruction to "continue" is **not** elevation approval.
- Approval must be recorded as explicit evidence in the canonical registry.
- A candidate may be stored, tested, merged as evaluation material, or displayed for review without becoming a Gold Star or runtime contributor.
- Automated validation must fail closed if a record claims Gold Star status without the required explicit review-and-approval evidence. Records already approved before this gate was introduced may be explicitly marked as legacy-grandfathered with a documented reason; that exemption may not be used for new elevations.
- Assistants and operators must not infer approval from conversational momentum or ambiguous instructions.

### 4.1 Canonical definition of Gold Star

A **Gold Star** has one constitutional meaning only: a fully evidenced exemplar that has completed rigorous validation, passed the required gates, been explicitly frozen, and is actively participating in the Guide's adaptive learning module.

- `USER_APPROVED_GOLD_STANDARD` is reserved exclusively for records meeting that complete contract.
- Historical approvals, recovered provenance, candidate lessons, incomplete fixtures, observers, and pending evidence records are **not Gold Stars** and must not be counted or treated as Gold Star learning authority.
- There is one canonical registry, one Gold Star definition, one authoritative count, and one active Gold Star learning set: the validated records carrying `USER_APPROVED_GOLD_STANDARD`.
- Any record that ceases to satisfy the full contract must be reclassified out of Gold Star status until the missing validation is completed.

## 8. Proportionate QA and resource stewardship

QA effort must be proportionate to the change's blast radius and the marginal confidence each test adds. The smallest test that establishes the required confidence is preferred. Additional tests require a concrete risk-based justification.

- Content-only Gold Star and registry additions use schema/integrity checks, targeted offline tests, and ordinary CI. Do not routinely issue visitor-facing production queries or compare Primary and Mirror after each such change.
- Runtime or provider-bank changes receive focused unit/contract tests and only the integration checks needed to validate the changed boundary.
- Routing, failover, shared-state, deployment-topology, or cross-server protocol changes require targeted Primary/Mirror integration verification.
- Retrieval changes require offline snapshot/fixture tests first; production retrieval tests are reserved for unresolved risks that cannot be established offline.
- Production smoke checks must be minimal, purposeful, and non-redundant. A health check, deployment identity check, and live query are distinct forms of evidence; do not run all three by habit.
- Prefer local fixtures, mocks, cached/versioned snapshots, and CI over Render requests, provider calls, or Pinecone operations when they provide equivalent evidence.
- Do not perform routine dual-service polling, broad production E2E suites, repeated log harvesting, or Pinecone enumeration for content-only changes.
- A coordinated release still must satisfy the two-server production contract. This standard changes the verification method for low-risk changes, not the required release identity: use the deployment system's existing evidence and escalate to direct parity checks only when a concrete discrepancy or integration risk exists.
- Record the reason whenever an expensive production check is retained, and state which uncertainty it resolves.

The detailed operating matrix is maintained in `docs/operations/SMALL_IS_BEAUTIFUL_QA_STANDARD.md`.
