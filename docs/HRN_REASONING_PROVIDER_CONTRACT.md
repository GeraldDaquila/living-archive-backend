# HRN Shared Reasoning Provider Contract

**Status:** Proposed architecture; not implemented or deployed  
**Scope:** Human Relational Navigator (HRN) reasoning-provider boundary  
**Authority:** Cowboy MCP remains the sole WordPress administration path  
**Safety constraints:** No changes to the live HRN plugin until the runtime boundary is verified. Do not modify protected `use_core.py`. Do not duplicate persistent Journey Ledger ownership.

## Decision

Use one HRN conversation pipeline with two isolated reasoning providers:

- **LLM provider:** open-ended semantic interpretation and nuanced contextual reasoning.
- **Deterministic provider:** bounded, explicit reasoning over structured evidence, journey state, and allowed conversational transitions.

The providers are alternatives behind a common contract, not two copies of the whole fractal workflow. They do not share mutable intermediate state, merge partial reasoning, or commit the Journey Ledger independently.

This document is a design specification only. The HRN plugin is administered on WordPress through Cowboy MCP and is not treated as if it were already implemented in this repository.

## Target pipeline

1. **Shared entrance:** receive visitor message, session identifier, conversation history, and committed Journey Ledger.
2. **Shared snapshot builder:** validate and normalize the request; construct an immutable, bounded working snapshot from the committed state plus the current visitor turn.
3. **Provider selector:** select one reasoning provider for the attempt. Provider selection and failure policy are explicit and observable.
4. **Isolated provider:** produce a structured reasoning result without writing persistent state.
5. **Shared result validator and governance:** validate schema, evidence references, uncertainty, permitted move, repetition, conversational progression, and humane-language constraints.
6. **Shared response boundary:** accept a provider-authored response or compose a bounded deterministic response from the validated result. Do not silently turn an invalid result into success.
7. **Single commit authority:** commit the response, next question/move, and ledger transition atomically once. A failed attempt must not partially advance the ledger.
8. **Shared response envelope:** return the visitor-facing response and explicit session/turn metadata consistently across providers.

## Provider-neutral input contract

The immutable input snapshot should contain:

- `contract_version`
- `request_id`
- `session_id` (stable across turns; never silently regenerated mid-journey)
- `visitor_turn_id` or equivalent idempotency key
- `visitor_message`
- `committed_ledger` (read-only snapshot)
- `recent_conversation` (bounded, ordered, role-labelled)
- `current_evidence_delta` (what the new turn adds or corrects)
- `known_observations` (visitor-reported facts, kept distinct from interpretations)
- `prior_moves` and `prior_questions` (for repetition/progression checks)
- `allowed_moves`, `closure_state`, and relevant policy constraints

The snapshot builder is the sole place that combines the current visitor turn with persisted context. Providers receive the same snapshot and cannot mutate it.

## Provider-neutral reasoning result

Each provider returns a typed result with at least:

- `contract_version`
- `provider_id` and `provider_version`
- `status`: success, insufficient_context, unsupported, or failure
- `evidence_delta`: references to the visitor contribution(s) actually used
- `observations`: supported observations, without inferred motives presented as facts
- `interpretation`: tentative and explicitly uncertain where appropriate
- `distinctions`: what is known versus unknown, and what should not be conflated
- `next_move`: one permitted move (for example, clarify, distinguish, deepen, reflect, or close)
- `move_rationale`: concise, inspectable reason tied to evidence and journey state
- `response_draft` or `response_plan`
- `proposed_state_delta`: proposed changes only; never a complete provider-owned ledger
- `limitations`: uncertainty or missing information that affects the result

The contract should not require providers to expose private chain-of-thought. It requires concise, auditable evidence references and decision rationale, not hidden internal reasoning traces.

## Deterministic provider workflow

The deterministic provider should be a bounded state-transition system, not a static answer bank and not a keyword-only imitation of an LLM.

1. Compare the current visitor contribution with the previous committed evidence.
2. Extract only supported observations and corrections using explicit rules.
3. Compute the new evidence delta and identify whether it changes the current relational question.
4. Consult prior moves/questions and completed micro-fractals.
5. Choose one allowed next move through explicit, ordered transition rules.
6. Compose a short response from bounded templates that incorporate the actual evidence delta.
7. Return the same provider-neutral result shape as the LLM.
8. Yield `insufficient_context` when ambiguity exceeds its rules rather than inventing motive or claiming semantic understanding it cannot support.

The deterministic provider may perform continuity, repetition, progression, uncertainty, and bounded response tasks reliably. It must not claim equivalence to open-ended LLM semantic interpretation.

## Shared governance invariants

- **One writer:** only the shared commit authority writes the persistent Journey Ledger.
- **One commit per visitor turn:** use an idempotency key or equivalent guard to prevent duplicate advancement.
- **No provider state bleed:** no mutable state, hidden scratchpad, or provider-specific partial ledger is passed to the other provider.
- **Evidence before interpretation:** distinguish reported behavior from inferred intent.
- **Delta before inquiry:** a new response must visibly incorporate the current visitor contribution before asking another question.
- **No unchanged-question loop:** reject a repeated question/move unless the system can state a concrete reason to revisit it.
- **Progression:** each turn must clarify, distinguish, deepen, reflect, or close; otherwise ask a genuinely different question or return an explicit insufficiency state.
- **Uncertainty discipline:** temporal association is not proof of causation; do not diagnose the other person or presume motive.
- **No fake success:** provider timeout, invalid schema, missing session state, or failed commit remains a failure/limited result in telemetry and is not disguised as a successful reasoning turn.
- **One response envelope:** provider choice does not change the external API/visitor UI contract.
- **No hidden double execution:** fallback behavior must be explicit; do not silently invoke both providers and blend their results.

## Failure and fallback policy

- A provider result is not committed until shared validation and response validation pass.
- A transient provider failure may select the deterministic provider only if the same immutable input snapshot and committed ledger are reused.
- If the deterministic provider cannot safely handle the input, return a humane, explicit limited response or retryable error; do not fabricate a completed fractal.
- Never increment the journey turn, mark a fractal complete, or overwrite the prior question merely because a provider call began.
- Record provider selection, failure class, validation outcome, and commit outcome without logging secrets or unnecessary sensitive visitor content.

## Acceptance tests

### Contract and isolation
1. Both providers accept the same frozen input snapshot and return schema-valid results.
2. Provider execution cannot mutate the snapshot or persistent ledger.
3. Forced LLM success and forced deterministic success each result in exactly one commit.
4. Forced LLM timeout/exhaustion reuses the same session, turn id, evidence snapshot, and prior committed ledger for deterministic recovery.
5. Invalid provider output and failed commit do not advance persistent state.
6. Replaying the same visitor-turn id does not create a second commit.

### Continuity and progression
Use the following three-turn fixture:

1. Visitor: “I keep initiating contact with a friend, and I want to understand what is happening between us.”
2. Visitor: “Lately, they have been aloof, even ghosting my texts without explanation. I noticed this behavioral change last when I declined loaning them some money.”
3. Visitor: “The long silence, evaded answers, and as mentioned ghosting my texts. Since there's no clear cut time as to when this behavior started, I keep wondering as to what triggered it.”

Acceptance:
- Turn 2 acknowledges that the timing after the declined loan stands out, without asserting causation; it may ask whether the friend explicitly connected the distance to that decision.
- Turn 3 reflects the silence and evaded answers, then advances from “what triggered it?” to a distinct question about whether the friend is willing to address the distance.
- No unchanged generic response/question across turns 2 and 3.
- The same session identifier is preserved, committed evidence includes the preceding turns, and the ledger advances once per accepted visitor turn.
- Both provider modes preserve uncertainty, agency, humane voice, and non-prescriptive posture.

### Regression matrix
Include missing/contradictory evidence, an ambiguous motive, a corrected visitor fact, repeat submission, provider timeout, malformed provider output, closure, a new-session request, and a valid request after a failed request. Verify response content, evidence references, state transition, response envelope, and persisted ledger—not merely HTTP status or string presence.

## Implementation sequence

1. Read-only trace of the live WordPress request/session adapter, snapshot builder, provider call, response composer, and ledger commit path using Cowboy MCP.
2. Capture the current live plugin version and file hash; reproduce the three-turn failure using a stable session and read back the committed ledger through an authorized diagnostic path.
3. Add a non-production contract fixture and deterministic provider prototype outside the live plugin.
4. Run the same fixtures against LLM success, deterministic success, and forced provider failure; inspect content and state transitions.
5. Integrate only at the verified provider boundary using a complete, reviewable file replacement and explicit rollback artifact.
6. Run regression, session continuity, response progression, closure, and browser-level visitor E2E.
7. Deploy only after all acceptance criteria pass. Otherwise keep production unchanged and report the exact failing gate.

## Explicit non-goals

- Rewriting or duplicating the complete LLM fractal workflow.
- Allowing providers to mutate or independently persist Journey Ledger state.
- Treating deterministic rules as equivalent to open-ended semantic reasoning.
- Changing production WordPress files while the current failure boundary remains unverified.
- Modifying protected `use_core.py`, changing embeddings, or re-embedding the corpus.
