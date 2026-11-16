# Small Is Beautiful QA Standard

**Status:** Operational standard  
**Authority:** USE Ecosystem Constitution, section 8  
**Scope:** Gold Star, registry, provider, retrieval, routing, and deployment changes

## Governing rule

Use the least expensive validation that reliably establishes the required confidence. QA is a risk-control function, not a ritual. More tests are not automatically better; a test is justified when it resolves a material uncertainty that cheaper evidence cannot resolve.

## Change-class matrix

| Change class | Default validation | Production verification |
|---|---|---|
| Gold Star content/metadata addition | Registry schema and integrity; targeted offline matching/authority tests; ordinary CI | No visitor query and no routine Primary/Mirror comparison |
| Gold Star transfer-review addition | Targeted offline transfer and abstention tests; ordinary CI | None routinely |
| Numbering/provenance correction | Ledger invariants, historical-gap and identity tests | None routinely |
| Provider prompt/contract change | Focused contract fixtures and provider-response mocks | One bounded integration check only if the changed provider boundary cannot be validated offline |
| Provider routing, cooldown, budget, or failover change | Unit tests for eligibility, ordering, cooldown and failure classification; mocked multi-provider exhaustion test | Targeted live check only for an unresolved external integration risk |
| Retrieval/scoring change | Versioned snapshot fixtures; relevance/abstention tests; no Pinecone enumeration | One bounded production retrieval check only if fixture evidence cannot settle the issue |
| Routing, 70/30 allocation, shared state, or Primary/Mirror protocol change | Offline tests plus focused integration tests for the changed boundary | Direct Primary/Mirror verification is required |
| Deployment infrastructure or service configuration change | Configuration validation and deployment checks | Verify affected service(s); verify both if shared topology or coordinated identity is affected |
| Production incident | Reproduce narrowly, inspect only relevant logs, validate the repair | Smallest targeted check that demonstrates recovery |

## Gold Star release path

1. Inspect the exact visitor-facing answer, approval evidence, canonical benchmark identity, provenance, and transfer boundaries.
2. Patch the canonical registry and qualitative transfer review on a branch.
3. Run registry integrity and targeted offline tests. Confirm structural contribution and deterministic-fallback eligibility separately.
4. Run the applicable CI checks and review the PR.
5. Merge the coherent change set.
6. Allow the established deployment mechanism to release it.
7. Confirm deployment completion using the existing deployment evidence. Do not automatically query both services or generate artificial visitor traffic.
8. Record only meaningful state changes in the operational manifest.

A production query is warranted only when the unresolved question is specifically about runtime behavior that cannot be established by code inspection, tests, or deployment evidence. Do not create traffic solely to obtain a log line.

## Production evidence: avoid redundant checks

Treat these as distinct evidence types:

- **Deployment evidence:** a service has completed the expected deployment.
- **Identity evidence:** a service is running the intended source revision.
- **Health evidence:** the service can respond to a health request.
- **Behavior evidence:** a representative request exercises a specific runtime behavior.

Choose only the evidence needed for the change. For a content-only Gold Star addition, offline tests plus normal CI and deployment completion are ordinarily sufficient. Do not routinely collect all four evidence types from both servers.

If the deployment platform already provides trustworthy completion and source-identity evidence, do not spend additional Render requests reproducing it. If the platform does not expose sufficient evidence, use one minimal check to close that gap.

## Render resource discipline

- No routine dual-service health polling after content-only deployments.
- No repeated log harvesting without a named diagnostic question.
- No broad production E2E query suites for ordinary Gold Star additions.
- No artificial traffic solely to prove a registry record was loaded.
- No Pinecone enumeration or synchronization during a resource-constrained period.
- Batch independent repository inspections and use CI/offline fixtures first.
- Keep production requests bounded, purposeful, and non-redundant.

## Escalation criteria

Escalate beyond the default only when one or more apply:

- A change crosses a service, provider, network, persistence, or routing boundary.
- CI or offline fixtures cannot represent the relevant failure mode.
- Deployment evidence is missing, contradictory, or indicates a failed release.
- Primary and Mirror are observed to disagree, or the change alters their coordination contract.
- A production incident or material visitor-facing regression is reported.
- A security, safety, data-integrity, or canonical-authority invariant is at risk.

When escalating, write down the specific uncertainty, the smallest test that can resolve it, and why cheaper evidence is insufficient.

## Reporting language

Report only what the evidence supports. Distinguish:
- merged from deployed;
- deployment completion from health;
- health from behavior;
- registry presence from actual runtime activation.

Do not claim production behavior was verified merely because tests passed or a deployment completed.
