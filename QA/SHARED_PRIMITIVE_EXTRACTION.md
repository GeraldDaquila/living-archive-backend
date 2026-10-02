# v487.83 Shared Primitive Extraction — Draft

This checkpoint is the first implementation of the shared substrate, but it remains isolated from
production.

## Extracted

The new `shared_intelligence_primitives.py` contains only small, authority-free transformations:

- source/evidence normalization;
- claim normalization with provenance references;
- epistemic tagging;
- synthesis-material packaging;
- canonical-doorway candidate normalization;
- explicit operation-result states;
- a minimal visitor-language leakage check.

## Deliberately absent

The module does not:

- route a visitor;
- select a specialist;
- call Groq or another provider;
- retrieve from the web or Pinecone;
- declare canonical authority;
- own a conversation;
- manage HRN relational state;
- manage FSD diagnostic state;
- generate final visitor prose;
- rewrite specialist voice.

## Why this shape

The archaeology showed that existing USE answer builders combine transformation, orchestration and
visitor composition. Extracting those functions whole would reproduce the coupling.

The new module therefore extracts the *data transformations* rather than the historical answer builders.

## Production status

No production file imports this module. `use_core.py` remains untouched and protected.

The next gate is integration testing against actual USE behavior. Only after that comparison passes
should a production seam be considered.
