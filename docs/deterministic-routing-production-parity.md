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
| SH-09 | I can't tell whether what I'm sensing in a relationship is real or something I'm projecting. | Production relational boundary opens HRN for this first-person projection inquiry; registry currently defaults to Guide | Known false negative / HRN parity gap |
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

The production test `tests/test_v489_85_relational_projection_routing.py` asserts that the query in SH-09 opens the relational boundary with reason `lived_relational_structure`, while a bounded Archive article search about projection stays outside HRN. The registry's current rule does not match the SH-09 wording and defaults it to `guide/direct`. A dedicated registry test now pins this as a known parity gap rather than allowing it to be mistaken for a pass.

This is an evidence-based mismatch, not a reason to add a broad relationship keyword rule. Any repair must preserve the production boundary's first-person, counterpart/relational, dynamic, inquiry, and bounded-resource suppression signals. SH-15 is sourced from the existing workplace-return regression family; it still requires a true history-dependent fixture from the relevant production tests before the history gate can be considered covered.

## Confirmed Catalogue parity gap from production fixtures

Production `tests/test_catalogue_resource_search_routing.py` treats broad explicit resource-discovery requests such as “Where can I find material about institutional responsibility?”, “Please recommend resources on stewardship,” and “What resources are available on stewardship?” as Catalogue searches. The isolated registry currently defaults these to Guide because its Catalogue patterns require narrower words such as `catalogue`, `catalog`, or `archive resources`. Dedicated registry tests now pin representative examples as known parity gaps. The correct repair must match the production resource-discovery intent while preserving the production exclusion for mixed explanatory questions such as “What is stewardship? Where can I find material about it?”; a simple `resources` keyword rule would be unsafe.
