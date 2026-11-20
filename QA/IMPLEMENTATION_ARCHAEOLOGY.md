# v487.82 Implementation Archaeology

This checkpoint maps the smallest currently identifiable USE implementation primitives against the
shared-intelligence disciplines validated in v487.81.

It is deliberately a **mapping exercise, not extraction**. No production runtime is changed.

## USE implementation map

| Shared discipline | Existing USE realization | Boundary |
|---|---|---|
| Inquiry / movement understanding | `_weighted_inquiry_profile`, `_inquiry_profile` | USE-specific macro inquiry/action semantics remain outside shared runtime. |
| Evidence normalization | `_parse_context_documents`, `_clean_evidence_text`, `_valid_doc_url` | Retrieval/source authority remains upstream. |
| Candidate ranking | `_candidate_sentences` | Candidate ranking is useful but its scoring vocabulary should not be copied blindly. |
| Claim separation | `_extract_claims` | Claim objects remain source-linked; epistemic treatment is currently USE-shaped. |
| Synthesis / visitor construction | `_build_factual_answer`, `_recommendation_answer`, `_build_lived_experience_answer`, `_unified_visitor_construction` | Construction logic contains historical/topic-specific exceptions and must be decomposed before reuse. |
| Canonical doorway proposal | recommendation/canonical-selection helpers | Proposal can be shared; final authority remains USE. |
| Visitor-language boundary | `_v487_generate_boundary`, `_v487_evidence_gap_boundary`, `_sanitize_visitor_output` | Boundary is partly orchestration-specific and must not become a hidden universal persona. |
| Explicit failure state | evidence-gap boundary plus surrounding fallback logic | Current legacy fallback behavior needs careful preservation/audit; shared state should not fabricate prose. |

## Archaeological conclusion

The reusable unit is **not** any one of the existing visitor-construction functions.

The likely extraction seams are smaller:

1. source/document normalization;
2. claim normalization with provenance;
3. epistemic tagging;
4. bounded synthesis material;
5. doorway-candidate normalization;
6. explicit operation-result construction.

Inquiry interpretation, provider choice, specialist routing, and visitor-facing realization remain higher-level
or mode-owned until implementation comparison proves otherwise.

## Critical finding

The current USE runtime mixes three different concerns inside the same historical neighborhood:

- reusable reasoning transformations;
- USE orchestration/authority;
- visitor prose composition.

Extracting whole functions would therefore reproduce the coupling we are trying to remove.

The next extraction should be **data-first and transformation-first**, not answer-builder-first.

## HRN comparison boundary

HRN's live implementation is not duplicated in this backend repository. The backend-side evidence currently
available is the validated relational contribution and adapter contract:

- specialist contribution validation;
- preservation of HRN's specialist voice;
- transport of relational movement/journey data;
- Guide-owned canonical integration.

Accordingly, HRN-specific conversation state and perspective movement are not candidates for extraction here.

## General Utility finding

`general_utility.py` remains an archaeological candidate, not a production target. Its evidence cleaning,
claim extraction, bounded state handling, and canonical-candidate concepts overlap with the shared disciplines,
but its answer-construction logic should not become the new common brain.

## Protected boundary

No changes are authorized here to:

- `use_core.py`;
- current production `main.py`;
- current production `main_v487_28_runtime.py`;
- live HRN plugin.

