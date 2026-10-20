# Deterministic-first routing: production parity gate

Status: design/QA only. This registry is not imported by `main.py` and must not be treated as production routing.

## Existing production behavior observed in `main.py`

The current `_guide_capability_route()` performs the following work, in order or at later arbitration points:

1. Hard deterministic guard for practical stewardship questions, returning Guide/direct before a model call.
2. Computes `_guide_route_fallback()` as a fallback result before invoking the model bank.
3. Invokes `route_with_model_bank()` for ordinary queries, so routine routing still incurs a model call today.
4. Accepts a model interpretation with route and mode fields.
5. Prevents a Formation route from taking ordinary practical stewardship questions unless Formation entry is explicit.
6. Can promote a Guide result to relationship navigation through `_relational_boundary_decision()`.
7. Can activate an approved Guide Node using the live/fresh WordPress node registry and semantic arbitration.
8. Validates route IDs against `_GUIDE_ROUTE_IDS`, validates modes, and handles missing/unavailable Guide Nodes.
9. Applies the protected-core risk profile through `_base._inquiry_profile()`, `_should_honor_protected_risk_profile()`, and `_guard_hypothetical_safety_route()`.

The isolated registry does not yet reproduce steps 5–9. It is therefore not production-parity complete.

## Complete route-ID inventory from production

The current `_GUIDE_ROUTE_IDS` set in production `main.py` contains:

- `guide`
- `relationship`
- `formation`
- `catalogue`
- `atlas`
- `navigator`
- `systems_ph`
- `safety`
- `glossary`
- `glyph`
- `case`
- `fsd`
- `guide_node`

The registry currently has explicit rules for catalogue, formation, FSD, glyph, Atlas, glossary, a high-signal subset of relationship navigation, and bounded initial rules for `navigator`, `systems_ph`, and `case`.

The `systems_ph` rule was tightened after review: naming the Philippine Systems Lens is not sufficient by itself. The query must contain an explicit invocation verb (for example, open/use/apply/run) adjacent to the surface name. Tests now assert that mention-only questions remain in Guide and explicit invocation selects the specialist. This is a conservative routing contract, not proof of production parity. These new rules are only explicit-surface subsets, not equivalents of production behavior. It still does not implement live `guide_node` arbitration. The safety override is not connected to the protected-core safety authority.

## Deterministic fallback route families observed

| Route | Existing bounded trigger / guard | Current registry status |
|---|---|---|
| safety | Protected-core inquiry risk profile and safety guards | Only accepts an explicit `safety_active=True`; not wired to protected core |
| fsd | `_is_fsd_request(query)` | Explicit-name subset only; natural-language diagnostic boundary not equivalent |
| glyph | explicit glyph/symbol/icon/mark plus lookup language | Added; parity tests still required |
| atlas | `_is_explicit_atlas_request(query)` | Added; current patterns are only an approximation |
| glossary | definition/meaning language | Added; target-term and ambiguity behavior need review |
| guide | conservative fallback for unbounded/open-ended inquiry | Added as default |
| relationship | `_relational_boundary_decision(query)` and model-route arbitration | Added high-signal subset only; does not implement production multi-signal boundary |
| formation | `_explicit_formation_entry_route(query)` plus post-model guard | Added high-signal subset only; exact preparation and entry language differ |
| catalogue | explicit resource-discovery task | Added; must be checked against the current catalogue route and access class |
| guide_node | active WordPress node registry + semantic arbitration | Not implemented in this registry |
| case | case navigator / case request guards | Explicit case-study retrieval subset added; production guards and access behavior unverified |
| navigator | supported production route ID; whole-Archive orientation intent | Explicit orientation-language subset added; production parity unverified |
| systems_ph | supported production route ID; Philippine systems inquiry | Explicit surface-name subset added; natural-language parity unverified |

## Verified isolated-test result

GitHub Actions run 47 for the deterministic routing registry completed successfully on commit `d142e5be449a154d0a9cbe5add7e8a74ecf0b4f5`. The job completed the `Run isolated registry tests` step successfully. The suite includes explicit regression coverage for glyph-meaning questions versus generic glossary matching, Catalogue-versus-case-study precedence, and case-study retrieval without a Catalogue mention. This confirms the isolated registry tests passed in that run; it does **not** establish production parity or visitor-facing end-to-end success.

An earlier run failed because `What is stewardship and why does it matter?` was classified as `glossary` rather than `guide`. A bounded exclusion was added to keep explanatory stewardship questions in the general Guide lane. Subsequent isolated CI runs have passed, including the latest run noted above.

## Non-negotiable integration gates

- Preserve protected safety authority; never infer safety solely from this registry's optional flag.
- Preserve Guide Node freshness and Level I/II arbitration. Do not replace live node evidence with hard-coded topic rules.
- Preserve current specialist availability/access controls, including the planned/not-available distinction.
- Preserve the full production FSD and relational boundaries, including multi-signal evidence and history-aware cases.
- Keep route selection separate from answer generation and canonical retrieval.
- Unknown or mixed requests stay in the Guide or ask for clarification; no second LLM call solely to classify.
- Shadow-compare registry decisions against current routing on a curated representative corpus before enabling it.
- Add tests for route/mode compatibility, precedence collisions, history-dependent cases, missing nodes, protected-risk behavior, and no-regression of ordinary Guide questions.
- Do not merge/deploy until tests execute and results are inspected and the parity gaps are resolved.

## Current disposition

The passing isolated suite is a necessary but insufficient gate. Bounded initial rules now exist for 12 of the 13 production route IDs; `guide_node` still requires live/fresh registry arbitration. The added rules for `navigator`, `systems_ph`, and `case` do not establish parity. Continue with route/mode compatibility tests, production-vs-registry shadow fixtures, and collision/precedence review. Do not import the registry into `main.py`, merge the PR, or deploy it until the gaps above are addressed.


The Philippine Systems Lens rule now requires explicit invocation intent rather than a surface-name mention alone, and negated invocation language (for example, “Do not open the Philippine Systems Lens”) is excluded. Dedicated tests cover mention-only, affirmative invocation, and negated invocation. Latest isolated registry CI run #59 passed; the separate broad v487 regression workflow for the same head was still running at last inspection.

## Shadow-comparison corpus: first review set

This is a review fixture list, not a claim that the registry matches production. For each prompt, record the current production route and mode, the registry route and mode, whether they differ, and the reason. Do not switch traffic based on this small set alone.

| ID | Query | Primary behavior to verify | Risk if mismatched |
|---|---|---|---|
| SH-01 | What is stewardship and why does it matter? | Ordinary explanatory inquiry remains Guide | False specialist handoff |
| SH-02 | Find case studies relevant to stewardship. | Case retrieval intent is recognized without requiring the Catalogue name | Missed case retrieval |
| SH-03 | Find case studies in the stewardship catalogue. | Catalogue-vs-case precedence matches current production semantics | Wrong evidence source |
| SH-04 | What does this glyph mean? | Explicit glyph meaning request is not swallowed by generic glossary | Wrong specialist |
| SH-05 | Open the Philippine Systems Lens. | Explicit surface invocation is recognized only if production allows it | Unsupported handoff |
| SH-06 | What is the Philippine Systems Lens? | Surface-name mention alone remains an explanatory Guide question | False specialist handoff |
| SH-07 | Do not open the Philippine Systems Lens. | Negated action is not treated as affirmative invocation | Reversed user intent |
| SH-08 | Please do not find case studies. | Negated retrieval intent is not treated as an affirmative specialist request | Reversed user intent |
| SH-09 | I can't tell whether what I'm sensing in a relationship is real or something I'm projecting. | Production relational boundary opens HRN; registry now matches this narrow fixture | Narrow fixture covered; broader relational parity remains open |
| SH-10 | Run a Fractal Systems Diagnostic on this organization. | FSD's full multi-signal production guard is preserved | False diagnostic activation |
| SH-11 | Where should I begin in the Living Archive? | Whole-Archive orientation behavior matches the current Navigator contract | Wrong entrance |
| SH-12 | Show me the map of this place. | Generic maps do not activate the Archive Atlas absent Archive-specific intent | False Atlas handoff |
| SH-13 | Open the Guide Node for this topic. | Live node freshness, availability, and access checks remain authoritative | Stale or unauthorized handoff |
| SH-14 | I feel unsafe right now. | Protected safety authority remains first and independent of registry keywords | Safety-boundary regression |
| SH-15 | I keep returning to the agreed deadline because the project scope changed afterward. My colleague says I'm making too much of it. I want to understand what is happening between us. | Preserve workplace/context-sensitive relational boundary and history-aware handling | Loss of relational context or over-routing |

### Recording contract

For every fixture, capture:

- fixture ID and exact query text;
- current production route, mode, and relevant decision reason;
- registry route, mode, confidence, and reason;
- whether the query depends on conversation history, live Guide Node data, access controls, or protected safety authority;
- mismatch classification: false positive, false negative, mode incompatibility, missing live evidence, or acceptable intentional difference;
- test added and reviewer disposition for every mismatch.

A blank production result is not a match. A registry decision is not accepted merely because it is deterministic. Any safety, access, stale-node, history-dependent, or route/mode-contract mismatch blocks integration. Populate SH-15 from an existing protected regression fixture rather than inventing a synthetic history and treating it as representative.

## Confirmed known mismatch from production regression fixture

The production test `tests/test_v489_85_relational_projection_routing.py` asserts that the query in SH-09 opens the relational boundary with reason `lived_relational_structure`, while a bounded Archive article search about projection stays outside HRN. The registry now has a narrow multi-signal rule requiring first-person language, a relational term, a dynamic interpretation/projection signal, and uncertainty/inquiry language. A paired bounded Archive-resource suppressor keeps the known article-search fixture out of the relationship route.

Dedicated registry tests cover the production positive fixture, the bounded Archive article-search negative fixture, and topic-only projection mentions. The rule is an intentionally narrow parity improvement, not a claim that it reproduces the full production `_relational_boundary_decision()`: counterpart signals, history-aware cases, and other relational patterns still require shadow fixtures. SH-15 is sourced from the existing workplace-return regression family; it still requires a true history-dependent fixture from the relevant production tests before the history gate can be considered covered.

## Catalogue resource-search parity: bounded rule added; latest CI passed

Production `tests/test_catalogue_resource_search_routing.py` treats broad explicit resource-discovery requests such as “Where can I find material about institutional responsibility?”, “Please recommend resources on stewardship,” and “What resources are available on stewardship?” as Catalogue searches. The registry now has a bounded task-intent predicate that mirrors the production predicate's resource nouns and retrieval verbs, including its explanatory-first exclusion. It does not route on the word `resources` alone.

The registry tests cover all ten positive examples from the production fixture plus the three negative/explanatory examples. On corrective commit `29a87c46c3eadd5eaaba68ddadce37a20ffdccfb`, the isolated registry workflow, broad v487 production-validation workflow, and mocked UI continuity workflow all completed successfully. These results verify those CI workflows on that commit; they do not prove route-by-route production parity or live visitor success. Native handoff payloads, history, access, live Guide Node arbitration, and the protected safety authority remain outside this isolated registry. Continue the full shadow comparison before considering integration.


## Current verified CI checkpoint — 2026-10-20

Corrective commit: `29a87c46c3eadd5eaaba68ddadce37a20ffdccfb`.

- Deterministic routing registry tests: run #89 — **success**.
- v487 production validation: run #2306 — **success**.
- Guide Woody mocked UI continuity contract: run #215 — **success**.

The registry tests had previously failed because a stale parity-gap test still expected the first-person projection fixture to remain in Guide after the narrow relational rule had been added. The stale test has been corrected to assert the intended relationship route. The three workflows above passed after that correction.

These are CI results, not a production release. PR #712 remains open and unmerged. No production wiring, WordPress change, or Render deployment is authorized by this work. Remaining gates include route/mode parity across all production route families, history-dependent relational cases, live Guide Node freshness/access, specialist availability, protected safety integration, and a curated production-versus-registry shadow comparison.


## Latest full CI checkpoint — 2026-10-20

On documentation checkpoint commit `447c59e2271e80e8a40593659560c06824883de3`, all three triggered workflows have now completed successfully:

- Deterministic routing registry tests, run #90.
- v487 production validation, run #2307.
- Guide Woody mocked UI continuity contract, run #216.

This is a green CI checkpoint for the isolated PR head. It does not convert the remaining parity gaps into passes and does not establish live visitor E2E success.

## Release-blocking gaps still open

1. **Protected safety authority:** the registry only accepts `safety_active=True`; it does not derive or connect to the protected-core safety boundary. Keep the authoritative production safety path unchanged.
2. **Guide Node arbitration:** the registry does not query the live/fresh WordPress Guide Node registry or reproduce access and availability checks.
3. **History-aware relationship handling:** the narrow projection fixture is covered, but the registry does not reproduce production relational history/context signals. The SH-15 fixture must come from a real existing production regression test; a synthetic query alone is insufficient.
4. **Specialist parity:** FSD, Formation, relationship, Atlas, glossary, Navigator, systems lens, and case rules remain bounded approximations rather than proven production-equivalent route/mode contracts.
5. **Shadow comparison:** no executed production-versus-registry shadow corpus is recorded here. The fixture table is a plan until both sides' actual decisions are captured.
6. **Live visitor E2E:** mocked UI continuity is a regression workflow, not proof that a real visitor request traverses the live WordPress frontend, backend, retrieval, and response path successfully.

Disposition: continue isolated test and parity work only. Do not wire the registry into `main.py`, merge PR #712, or deploy until these release gates are addressed and independently verified.


## SH-15 source verification — 2026-10-20

The SH-15 wording is grounded in the existing production regression fixture in `tests/test_v489_226_relational_return_workplace_doorway_parity.py`. Its original query is:

> I keep returning to the agreed deadline because the project scope changed afterward. My colleague says I'm making too much of it. I want to understand what is happening between us.

That test family verifies workplace-change fit, a verified canonical Conflict & Trust Arc candidate, and rejection of an unqualified generic Orientation page. Related coverage exists in `tests/test_v489_86_relational_return_topic_fit.py` and `tests/test_v489_89_relational_return_clustered_topic_evidence.py`, including recurring-argument repair-resource recovery and rejection of broad decoys.

**Important distinction:** this is a real production regression fixture with workplace/context-sensitive relational intent, but the quoted query is itself a single-turn input. It does not, by itself, prove history-dependent routing. The registry currently routes it through the broad explicit relationship pattern, but that is not equivalent to production's full relational-return resource-selection and conversation-history behavior. SH-15 must therefore remain a parity blocker until actual multi-turn history/context input and route/mode outcomes are captured on both sides. Do not mark the history gate passed based on this fixture alone.


## Workplace-return fixture contract test — 2026-10-20

The isolated registry now has a contract test for the exact single-turn workplace-return query sourced from `tests/test_v489_226_relational_return_workplace_doorway_parity.py`. It asserts the bounded relationship/delegated-journey route and its rule source. This is a route-level regression check only: it does not assert canonical resource selection, multi-turn history, or the production relational-return pipeline.

On commit `73a6c2eb900ad297a7b6f152560114c5bd93e785`, all three triggered workflows completed successfully:

- Deterministic routing registry tests, run #94 — success.
- v487 production validation, run #2310 — success.
- Guide Woody mocked UI continuity contract, run #219 — success.

These results validate the isolated registry tests and the existing production/UI regression suites on this commit. They do not establish production-versus-registry shadow parity, live visitor end-to-end success, or release readiness. PR #712 remains open and unmerged; production routing and protected files remain unchanged.

## Latest verified CI checkpoint — 2026-10-20 (commit `7e94643a6d919837a3447340c019e51032183c1c`)

All three workflows have now completed successfully on the current registry code/test commit:

- Deterministic routing registry tests, run #97 — **success**.
- v487 production validation, run #2312 — **success**.
- Guide Woody mocked UI continuity contract, run #221 — **success**.

The registry test update adds explicit collision-precedence coverage for FSD, glyph meaning, and Catalogue/case-study requests, plus a mixed-negation request that must remain in Guide; it also removes a duplicate relational projection test.

This checkpoint establishes that these workflows passed on this commit. It does **not** establish route-by-route production parity, protected safety integration, live Guide Node arbitration, multi-turn history parity, or live visitor E2E success. The shadow comparison remains unexecuted. PR #712 remains open and unmerged; no production wiring or deployment is authorized.


## Negation-scope correction and latest CI checkpoint — 2026-10-20

On registry/test commit `9659d20dbb6bdba6081bdf928a11a70706de90ab`, all three workflows completed successfully:

- Deterministic routing registry tests, run #104 — **success**.
- v487 production validation, run #2312-equivalent workflow for this head (run ID `39345101421`) — **success**.
- Guide Woody mocked UI continuity contract, run #225 — **success**.

The registry now distinguishes a coordinated negated task from an explicit contrastive clause. “Please do not open the Philippine Systems Lens or find case studies” stays in Guide, while “Do not open the Philippine Systems Lens, but find case studies” routes to case-study lookup. This is a bounded English-pattern correction, not complete natural-language negation handling; other clause structures still need fixtures.

These CI results do not establish production-versus-registry shadow parity or live visitor E2E success. The shadow comparison has not been executed. Protected safety authority, live Guide Node freshness/access, history-aware relational handling, specialist availability, and complete route/mode parity remain release blockers. PR #712 stays open and unmerged; production wiring and deployment remain prohibited until those gates are addressed.
