# Guide Node Registry — QA Matrix v488.18

## Release state

Draft only. No production deployment.

## Structural tests

1. Registry contains only approved active nodes.
2. Every active node has a canonical HTTPS URL on geralddaquila.com.
3. Duplicate node IDs are rejected.
4. Invalid access classes are rejected.
5. Disabled/candidate records never appear in the active endpoint.
6. Navigation endpoint can represent both classic menus and wp_navigation.
7. Navigation inspection does not alter WordPress navigation.

## Visitor-routing tests

### Direct node questions

A natural question clearly seeking a glossary definition should be eligible for the Living Glossary.

A natural question asking where to understand a recurring organizational systems problem should be eligible for FSD.

A natural question asking about Philippine institutional/cultural systems should be eligible for the Philippine Systems node.

A natural question asking how to enter the Institute case collection should be eligible for the Case Library gateway.

### Buried-node tests

A visitor must be able to reach a substantive node without knowing its menu path.

Examples:

- "Where can I explore the Archive's definitions of its key terms?"
- "I keep seeing the same organizational pattern. Is there somewhere I can examine where the system is stuck?"
- "I want to understand Philippine society through the systems framework on this site."
- "I have a leadership problem and want to explore relevant cases rather than read random articles."
- "Where can I find the Learning Arcs?"

### Negative tests

The Guide must not route merely because a question contains a node title.

Examples:

- "What does glossary mean?" should not automatically open the Living Glossary.
- "What is an atlas?" should not automatically open the Stewardship Case Atlas.
- "Tell me about the Philippines" should not automatically bypass the Guide's normal reasoning if the question is broad enough to warrant orientation.

### Access-boundary tests

- Never claim restricted/purchase material is public.
- Never bypass a password-protected destination.
- If a mixed-access gateway is selected, preserve its native access explanation.
- If the best destination is restricted, the Guide may identify it but must preserve the access boundary.

### Native-tool tests

The Guide must hand off to a native tool when that tool owns the experience.

It must not recreate:

- FSD diagnostic logic.
- Living Glossary definition retrieval.
- Glyph Finder identity/search logic.
- HRN relational conversation.
- Case Navigator case inference.

The node layer is a doorway, not a second specialist.

## Regression gates

Before production integration:

- Protected `use_core.py` unchanged.
- Existing v488.17 Philippine Systems handoff unchanged.
- Existing FSD handoff unchanged.
- Existing Glossary handoff unchanged.
- Existing Glyph Finder handoff unchanged.
- Existing specialist route IDs unchanged.
- Ordinary Guide responses unchanged.
- No machine-language visitor fallback introduced.
- No frontend routing change until backend contract is verified.
