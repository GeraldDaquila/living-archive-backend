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

## Deterministic fallback route families observed

| Route | Existing bounded trigger / guard | Current registry status |
|---|---|---|
| safety | Protected-core inquiry risk profile and safety guards | Only accepts an explicit `safety_active=True`; not wired to protected core |
| fsd | `_is_fsd_request(query)` | Added; parity tests still required |
| glyph | explicit glyph/symbol/icon/mark plus lookup language | Added; parity tests still required |
| atlas | `_is_explicit_atlas_request(query)` | Added; current patterns are only an approximation |
| glossary | definition/meaning language | Added; target-term and ambiguity behavior need review |
| guide | conservative fallback for unbounded/open-ended inquiry | Added as default |
| relationship | `_relational_boundary_decision(query)` and model-route arbitration | Added high-signal subset only; not equivalent |
| formation | `_explicit_formation_entry_route(query)` plus post-model guard | Added high-signal subset only; not equivalent |
| catalogue | explicit resource-discovery task | Added; must be checked against the current catalogue route and access class |
| guide_node | active WordPress node registry + semantic arbitration | Not implemented in this registry |
| case | case navigator / case request guards | Not implemented in this registry |
| other supported route IDs | `_GUIDE_ROUTE_IDS` in `main.py` | Must be enumerated and mapped before integration |

## Non-negotiable integration gates

- Preserve protected safety authority; never infer safety solely from this registry's optional flag.
- Preserve Guide Node freshness and Level I/II arbitration. Do not replace live node evidence with hard-coded topic rules.
- Preserve current specialist availability/access controls, including the planned/not-available distinction.
- Keep route selection separate from answer generation and canonical retrieval.
- Unknown or mixed requests stay in the Guide or ask for clarification; no second LLM call solely to classify.
- Shadow-compare registry decisions against current routing on a curated representative corpus before enabling it.
- Add tests for route/mode compatibility, precedence collisions, history-dependent cases, missing nodes, protected-risk behavior, and no-regression of ordinary Guide questions.
- Do not merge/deploy until tests execute and results are inspected.

## Verification note

The current registry unit tests and workflow are committed on the feature branch. A workflow run or green status has not yet been confirmed by the available GitHub status/run query. Do not represent the tests as passing until a real run is visible and successful.
