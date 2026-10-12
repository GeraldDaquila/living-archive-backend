# Cross-Mode Capability Audit — v487.80

This audit compares the recovered historical USE capabilities with the evolved HRN contract.

## Findings

### Shared primitives worth standardizing
- **Inquiry / movement interpretation:** shared, but the input semantics differ. USE interprets macro intent; HRN interprets conversational movement. A common representation should expose both rather than collapse them.
- **Evidence normalization:** shared. Source material must remain distinguishable from synthesis.
- **Claim separation:** shared. Never fuse independent source propositions into an unsupported composite.
- **Synthesis:** shared at the discipline level. Each mode supplies its own synthesis grammar.
- **Epistemic boundaries:** shared. Interpretation, inference, and supported material should remain distinguishable.
- **Visitor-language realization:** shared. Internal structures must not leak into visitor prose.
- **Canonical doorway proposal:** shared. The active mode can propose; USE remains authoritative for final navigation.
- **Explicit operation states:** shared. Success, delegation, retryable failure, and unavailable states should be machine-readable.
- **Provider arbitration:** candidate shared primitive. Do not standardize until HRN live arbitration and USE core arbitration are compared under failure and quota conditions.

### Capabilities that should remain bounded
- **HRN:** relational conversation state, living-fractal progression, perspective movement, perspective delta, question-led steering, spiral/journey semantics.
- **FSD:** systems/fractal diagnostic reasoning.
- **USE:** macro routing, specialist delegation, contribution integration, final canonical authority.

## Important architectural result

The correct common layer is **not a universal conversation manager**.

It is a set of reusable reasoning disciplines with explicit interfaces.

The common layer must be capable of serving a relational specialist without turning the specialist into a general chatbot, and of serving general inquiry without importing relational behavior into every question.

## Candidate interface shape

A future shared contribution may carry:
- operation status;
- inquiry/movement representation;
- evidence items;
- normalized claims;
- synthesis material;
- epistemic classifications;
- visitor-language draft;
- doorway candidates;
- provenance / source identifiers.

Authority remains outside the substrate.

## Promotion rule

A primitive moves from candidate to platform standard only after at least two operating modes demonstrate that:
1. they need the same transformation;
2. the transformation can be expressed without domain-specific semantics;
3. the shared form reduces duplication;
4. the shared form does not reduce the quality of either mode.

This is a research result, not a production implementation.
