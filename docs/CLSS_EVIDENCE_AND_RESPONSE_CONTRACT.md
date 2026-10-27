# CLSS Provider-Independent Evidence and Response Contract

**Status:** Implementation specification draft. Governing model: [Issue #998](https://github.com/GeraldDaquila/living-archive-backend/issues/998). Questionnaire draft: [docs/CLSS_STEWARDSHIP_QUESTIONNAIRE_DRAFT.md](./CLSS_STEWARDSHIP_QUESTIONNAIRE_DRAFT.md).

This contract is shared by the LLM reasoning path and deterministic fallback. It does not authorize a remote LLM integration or change the current session-only privacy boundary.

## 1. Design invariants

1. The model reasons from the same normalized evidence regardless of provider.
2. Visitor answers remain distinguishable from system inferences.
3. Every substantive finding must cite one or more evidence item IDs.
4. Missing or unknown information is a gap, never negative evidence.
5. Third-party mode does not infer private intent or motive.
6. No scores, rankings, diagnoses, or automatic suitability decisions.
7. The LLM may enrich contextual reasoning, but may not override these invariants.
8. The fallback may be narrower than the LLM, but must still identify evidence, explain a supported tension or gap, and offer a practical next step.
9. No network transmission or persistence is introduced by this specification.

## 2. Normalized evidence item

Conceptual JSON shape:

```json
{
  "evidence_id": "ev-001",
  "prompt_id": "conduct-episode",
  "dimension": "conduct",
  "answer_text": "Exact visitor-supplied answer text",
  "source_type": "first_hand_observation",
  "context": ["Only context explicitly supplied by the visitor"],
  "affected_parties": ["Team members"],
  "observations": ["Observable action described by the visitor"],
  "reported_effects": ["Effect described by the visitor"],
  "visitor_interpretation": ["The visitor's own interpretation"],
  "counterevidence": [],
  "uncertainties": [],
  "provenance": {
    "mode": "third_party",
    "captured_at_runtime": true,
    "source_prompt_ids": ["conduct-episode"]
  }
}
```

### Allowed values

- `dimension`: `commitment`, `conduct`, `consequences`, `coherence`, `accountability`, `counterevidence`, `correction`, `unknown`.
- `source_type`: `self_report`, `first_hand_observation`, `documented_outcome`, `second_hand_report`, `interpretation`, `unknown`.
- `mode`: `self`, `third_party`.

The schema is a logical contract, not a mandate to add unnecessary form fields. If source type is not explicitly captured, store it as `unknown`; do not guess. Preserve the exact answer separately from any extracted claims.

## 3. Candidate coherence finding

The reasoning layer may create candidate findings. Each is an inference and must remain distinct from visitor evidence.

```json
{
  "finding_id": "finding-001",
  "finding_type": "supported_tension",
  "statement": "A concise, direct statement of the possible tension",
  "service_obligation": "The relevant responsibility or service obligation in context",
  "supporting_evidence_ids": ["ev-001", "ev-003"],
  "counterevidence_ids": ["ev-004"],
  "possible_alternatives": ["A plausible contextual explanation"],
  "consequences": [
    {
      "statement": "A consequence stated as observed or as a possibility",
      "status": "reported",
      "evidence_ids": ["ev-003"]
    }
  ],
  "material_unknowns": ["A fact that could change the interpretation"],
  "confidence_basis": "Explain the evidence basis in plain language, not a numeric score",
  "next_observation": "What evidence would distinguish the explanations"
}
```

Allowed `finding_type` values:
- `supported_tension`
- `mixed_evidence`
- `insufficient_evidence`
- `no_defensible_tension`

Confidence must be expressed through the evidence basis and limits, not a numeric person score. A possible consequence must not be rewritten as an observed fact. The finding must never claim that a third party's private motive is known.

## 4. Canonical response object

Both paths must populate the same visitor-facing contract:

```json
{
  "mode": "third_party",
  "path": "deterministic_fallback",
  "central_incoherence": {
    "text": "Direct finding or explicit statement that none is established",
    "finding_type": "supported_tension",
    "evidence_ids": ["ev-001", "ev-003"]
  },
  "why_it_matters": {
    "text": "Proportionate explanation of the impact",
    "evidence_ids": ["ev-003"]
  },
  "what_the_evidence_says": [
    {
      "text": "Connected evidence, with source type preserved",
      "evidence_ids": ["ev-001", "ev-003"]
    }
  ],
  "what_could_change_the_interpretation": [
    {
      "text": "Counterevidence, alternative explanation, or material unknown",
      "evidence_ids": ["ev-004"]
    }
  ],
  "what_to_do_next": {
    "action": "Concrete, proportionate next step",
    "owner": "Visitor, role-holder, or jointly agreed party when known",
    "observable_indicators": [
      "Observable sign that the next step occurred or behavior changed"
    ]
  },
  "limits": [
    "Relevant limitation, not a generic disclaimer that obscures the finding"
  ]
}
```

The `path` field is operational metadata and should not be used to imply that one path is more trustworthy. It may be hidden from visitors unless needed for transparent system status.

## 5. Shared validation rules

Reject or repair an output when:
- a finding contains no supporting evidence IDs;
- an evidence ID does not exist in the input evidence set;
- a statement marked observed has only interpretive or second-hand support;
- the output states an inferred motive as fact;
- an unknown is treated as proof against a person;
- a consequence is stated as certain when the evidence only supports a possibility;
- counterevidence supplied in the input is omitted where it materially changes the interpretation;
- the output offers only generic advice and no case-specific action;
- the output scores, ranks, diagnoses, or decides suitability.

If repair fails, return the deterministic fallback. If the fallback cannot support a specific tension, it must explicitly identify the information gap and a focused way to investigate it.

## 6. Deterministic fallback algorithm

1. Validate and normalize all answers without rewriting the original answer text.
2. Group evidence by the canonical stewardship dimensions.
3. Identify possible cross-dimension tensions only where relevant evidence exists on both sides.
4. Gather counterevidence and context before selecting a candidate.
5. Prefer the most consequential *supported* tension; do not rank people or count keyword occurrences.
6. If evidence is mixed, state both sides and identify the observation that would distinguish them.
7. If evidence is insufficient, identify the most decision-relevant gap.
8. Populate the canonical response object and apply the shared validation rules.
9. Compose clear, natural prose using a small set of structural templates that accept evidence-linked content—not generic paragraphs disconnected from the case.

A deterministic implementation must not pretend to have semantic abilities it does not have. If reliable cross-answer reasoning is not supported by the available implementation, choose the insufficient-evidence path rather than overclaim.

## 7. LLM adapter contract

The LLM receives:
- the normalized evidence set;
- the mode;
- the governing question and six-dimension coherence cycle;
- the allowed finding types;
- the canonical response object shape;
- the evidence and privacy rules.

The LLM returns only a candidate response object. A shared validator checks it before presentation. Do not expose raw provider output directly to the visitor. Provider timeout, unavailable credentials, malformed output, or validation failure must fall back to the deterministic path.

Any actual remote invocation requires a separately approved privacy design, explicit visitor-facing disclosure, and tests proving what data leaves the browser, where it goes, and whether it is retained.

## 8. Regression suite

| Case | Input characteristics | Required result |
|---|---|---|
| Strong supported tension | Specific commitment, repeated conflicting conduct, concrete impact | Name tension directly; cite evidence on both sides; action and observable indicators |
| Mixed evidence | Concern plus documented repair or counterexample | Preserve both; specify what would show sustained change |
| Contextual explanation | Unilateral decision during genuine time pressure, with explanation and follow-up | Do not mislabel as a stewardship failure; test proportionality and accountability |
| Insufficient evidence | Broad labels or reputation, no concrete example | State evidence gap and request a focused example |
| No defensible tension | Evidence aligns with the service obligation | Do not invent a concern; identify any remaining non-material unknown |
| Conflicting sources | First-hand account differs from second-hand report | Preserve provenance and disagreement; suggest fair verification |
| Third-party intent unknown | Silence or behavior is used to infer inner commitment | Do not claim motive or willingness; phrase as unknown |
| Repair and progress | Initial failure followed by a concrete correction | Include repair and observable change; do not freeze the person in the initial failure |
| Missing answer | One or more prompts unanswered | Treat only as missing information; no adverse inference |
| LLM invalid response | Missing citations, unsupported claims, malformed response | Reject and use validated fallback |

## 9. Acceptance gate

The schema is ready for implementation only when:
- each questionnaire prompt maps to one or more canonical dimensions;
- the evidence model preserves provenance and original answers;
- both paths can produce the canonical response object;
- validators can enforce evidence references and prohibited claims;
- the regression cases are executable tests, not only documentation;
- privacy review explicitly preserves or approves changes to session-only processing.

This document defines a contract. It does not claim the existing WordPress plugin or production site implements it yet.
