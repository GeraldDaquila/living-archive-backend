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

The registry currently has explicit rules for catalogue, formation, FSD, glyph, Atlas, glossary, a high-signal subset of relationship navigation, and bounded initial rules for `navigator`, `systems_ph`, and `case`. These new rules are only explicit-surface subsets, not equivalents of production behavior. It still does not implement live `guide_node` arbitration. The safety override is not connected to the protected-core safety authority.

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

GitHub Actions run 7 for the deterministic routing registry completed successfully after commit `e0cb763f3c27ca415f9e9a9d222bf22b75b3de46`. The job completed the `Run isolated registry tests` step successfully. This confirms the isolated registry tests passed in that run; it does **not** establish production parity or visitor-facing end-to-end success.

The earlier run failed because `What is stewardship and why does it matter?` was classified as `glossary` rather than `guide`. A bounded exclusion was added to keep explanatory stewardship questions in the general Guide lane. The passing run is associated with the correction.

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
