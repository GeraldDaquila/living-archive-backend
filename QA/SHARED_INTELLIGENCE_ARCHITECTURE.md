# Shared Intelligence Architecture — v487.80 design checkpoint

## North Star

Give the visitor an elegant, unified surface while keeping the underlying system capable of
deep reasoning, specialist depth, canonical evidence handling, graceful failure, and coherent
navigation.

## Architectural decision

Do not create a second general-purpose "brain" beside HRN.

Instead, standardize the reusable reasoning disciplines that emerged across the historical USE
lineage and HRN, while preserving bounded operating modes.

### Layers

1. **USE / The Guide — macro conductor**
   - understands the visitor's request at the macro boundary;
   - decides whether to retrieve, answer directly, delegate to a specialist, or use general mode;
   - owns orchestration and final canonical doorway authority.

2. **Shared Intelligence Substrate — common reasoning disciplines**
   - inquiry/movement understanding;
   - evidence normalization and claim separation;
   - synthesis;
   - epistemic boundary handling;
   - visitor-language realization;
   - canonical doorway proposal;
   - explicit success/delegate/retry/unavailable states.

3. **Bounded operating modes**
   - **General:** broad Archive questions and ordinary navigation/conceptual inquiry.
   - **HRN:** relational lived experience and perspective movement.
   - **FSD:** systems/fractal diagnosis and navigation.
   - future specialists as needed.

## Why

Historical USE code demonstrates valuable breadth, but its implementations are heavily coupled to
topic-specific exceptions. HRN demonstrates a richer model of conversational depth and movement.
The correct synthesis is therefore to standardize invariants and interfaces, not merge their old
implementations.

## Non-goals

- no production runtime wiring in this checkpoint;
- no changes to HRN plugin;
- no changes to protected use_core.py;
- no replacement of specialist-owned voice;
- no independent routing authority inside the substrate;
- no web retrieval inside the substrate;
- no automatic promotion of the current v487.79 General Utility extraction.

## Promotion criteria

A shared capability may become platform-wide only when:
- it is demonstrably useful in more than one bounded mode;
- it has a clear contract;
- failure is explicit rather than fabricated;
- it does not usurp routing or canonical authority;
- it can be tested independently;
- adopting it simplifies the overall architecture rather than adding another layer.
