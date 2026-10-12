# v487.81 Cross-Mode Behavioral Validation

## Gate result

The comparison has moved from a list of proposed interfaces to explicit case assertions.

The harness now verifies that the same reasoning *disciplines* recur across representative USE and
HRN operating situations without making their internal semantics identical.

## Shared disciplines supported by the comparison

- evidence normalization;
- claim separation;
- epistemic boundaries;
- synthesis as a transformation;
- visitor-language boundary;
- explicit operation states.

These are suitable candidates for a shared infrastructure layer, subject to implementation-level
regression testing.

## Shared, but authority-sensitive

**Inquiry / movement representation** is common infrastructure only as a neutral carrier. USE may
populate macro intent; HRN may populate conversational movement. The shared layer must not choose
between those meanings.

**Doorway proposal** is a common proposal mechanism. Final canonical authority remains with USE.

**Retry state** is common infrastructure. Provider selection and specialist-specific recovery remain
outside it until independently verified.

## Explicitly not shared

HRN continues to own:
- relational conversation state;
- question-led steering;
- living-fractal progression;
- perspective movement and perspective delta;
- specialist voice;
- spiral/journey semantics.

USE continues to own:
- macro routing;
- specialist delegation;
- contribution integration;
- final canonical authority.

Safety interruption/routing remains outside the generic reasoning grammar.

## Important correction to the previous stage

The earlier harness encoded many values as unconditional booleans. That was not a meaningful behavioral
test. v487.81 replaces that with structural assertions over case-level boundaries, so a future change
can actually break the harness rather than merely update a table of claims.

## Next gate

The next step is implementation archaeology: identify the smallest existing functions that realize the
validated shared disciplines, map duplication across USE and HRN, and only then extract a shared runtime
module.

No production code should be changed until that mapping is complete and its regression suite is in place.
