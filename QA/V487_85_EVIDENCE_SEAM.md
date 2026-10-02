# v487.85 — Evidence Normalization Production Seam

This release advances exactly one shared-substrate transformation into production:
already-parsed USE documents now pass through the shared evidence normalizer and are
converted immediately back into the legacy dictionary shape expected by the current
visitor construction/runtime.

The seam is intentionally narrow. It does not alter:
- USE routing;
- Groq/provider selection;
- Pinecone retrieval;
- canonical authority;
- HRN/FSD specialist behavior;
- visitor-facing answer construction;
- use_core.py;
- main_v487_28_runtime.py.

## Before / after

Before:
use_core._parse_context_documents(...) -> legacy document dictionaries

After:
use_core._parse_context_documents(...) -> shared evidence normalization -> legacy document dictionaries

The behavioral target is equivalence for the document transformation, not a new answer policy.

CI status must be observed before this seam is treated as merge-ready.
