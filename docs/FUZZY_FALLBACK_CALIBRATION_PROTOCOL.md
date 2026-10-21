# Fuzzy Relevance — Deterministic Fallback Calibration Protocol

## Purpose

Test whether the existing shadow-only fuzzy relevance scorer can improve the quality of The Guide's deterministic fallback when LLM providers are genuinely exhausted, without changing the LLM-primary / deterministic-fallback architecture or the visitor experience.

This is an evaluation protocol, not authorization to enable fuzzy scores in live decisions.

## Immutable runtime contract

- LLM providers remain the primary reasoning path.
- The current deterministic recovery remains authoritative when the provider bank is exhausted or the composition path fails safely.
- Fuzzy scores must not alter candidate eligibility, ordering, selection, routing, response text, doorway choice, safety behavior, or response latency.
- Do not modify protected `use_core.py`, the frozen stewardship gold-standard fixture, or its lock.
- Do not re-embed the corpus or change the embedding schema.
- Do not deploy evaluation-only changes.

## Evaluation cohort

Separate these cohorts in reports; do not combine them into one score:

1. **Provider-bank exhausted:** the normal provider-bank call returns no composition result and the current deterministic recovery supplies the response.
2. **Composition exception:** the composition path raises and the current safe deterministic recovery supplies the response.
3. **Provider timeout / individual provider failure:** record separately when identifiable; do not assume it is equivalent to complete provider-bank exhaustion.
4. **LLM-served:** the LLM produces the visitor response. This cohort is not evidence of fuzzy improvement to deterministic fallback and must not be counted in fallback efficacy metrics.
5. **Other deterministic paths:** bounded, question-class-specific recovery paths that bypass general composition should be labeled separately.

Only cases in cohorts 1 and 2 should be combined if the study explicitly reports both cohorts and their separate results. Cohorts 3 and 5 require their own analysis unless their exact pathway semantics are verified.

## Case capture and replay

Prefer already available, non-sensitive test cases and intentionally simulated provider-exhaustion cases. Do not add production instrumentation, log visitor question text, or store personal data merely to populate the experiment.

For each replay case, preserve:

- a stable case identifier;
- the provider/fallback pathway label;
- the visitor query, with personal or sensitive details removed;
- the canonical candidate set supplied to the existing deterministic selector;
- the unchanged deterministic selection (or no-selection result);
- fuzzy dimension scores computed over the same candidate set;
- an independently assigned relevance judgment and rationale, when available;
- whether the candidate set itself contains a resource that directly answers the query.

If real production cases are ever proposed, first establish an approved privacy-safe collection method and data-retention boundary. This protocol alone does not authorize production collection.

Replay the deterministic and shadow assessments offline. The fuzzy scorer must not run synchronously on the visitor's critical path for this study. If the exact eligible candidate set cannot be reconstructed faithfully, label the case non-comparable rather than implying a valid paired result.

## Judgment and scoring

Use a reviewer who did not author the candidate pair where practical. Reviewers should see the query and candidate content, but should not see which candidate the fuzzy scorer prefers until they record their relevance judgments.

For every case, classify the outcome as one of:

- **Potential recovery:** deterministic selector misses or declines a directly relevant candidate, while fuzzy ranking prefers it.
- **Correct unchanged baseline:** deterministic selector already chooses a directly relevant candidate.
- **Potential regression:** fuzzy ranking prefers a less relevant or insufficient candidate over the better-supported option.
- **Both insufficient:** neither approach has a directly relevant candidate; preserve conservative no-recommendation behavior.
- **Tie / ambiguous:** evidence does not support a defensible distinction.

Report counts and rates for every class, score margins, ties, candidate-set insufficiency, reviewer agreement, and cohort sizes. Keep simulated, correlated paraphrase families, and independently reviewed cases separate. Never promote a metric by excluding a failure after seeing the result; any exclusion must have a documented, predeclared reason.

## Observed simulated replay — 2026-10-22

Latest inspected replay commit: `37aa0f2aca5628559edac3993bc39c7a557dca06`. These seven cases are all deliberately simulated; the expected-relevance labels are authored assumptions, not independent human ground truth.

- Across the five provider-bank-exhaustion cases: deterministic matched the authored expectation in 3/5; fuzzy counterfactual matched in 2/5; there were two ties. This tiny synthetic cohort is not a performance estimate.
- The consultation case remains unresolved: deterministic returned no selection and fuzzy tied the candidates.
- The deliberately lexical consultation case was a **potential recovery** in this simulation: deterministic selected a status-update resource while fuzzy preferred the participation resource.
- The insufficient-candidate case preserved conservative no-selection for deterministic, while fuzzy tied. The case is classified separately and is not counted as evidence of fuzzy correctness.
- The adversarial title-overlap case is a **potential regression**: deterministic selected the resource whose body states the requested current permit form and deadline; fuzzy preferred a decoy whose title overlaps the query but whose body explicitly lacks those details. The recorded scores were 0.1500 for the evidence-bearing candidate and 0.3891 for the decoy. The decoy's strongest dimensions were procedural specificity (0.5889), title overlap (0.5000), and body overlap (0.3333); the evidence-bearing candidate's strongest was body overlap (0.5833). This indicates the aggregate score rewards the decoy's procedural cue/title match more than the body evidence that actually answers the request. It does not prove a single feature is solely responsible; weights and interactions jointly determine the result.
- The composition-exception case was a correct unchanged baseline. The individual-provider-failure case is reported separately and excluded from provider-bank-exhaustion/composition-exception metrics.

These classifications come from the replay's author-authored labels and candidate descriptions. They show a specific failure mode worth independent review; they do not establish general relevance accuracy. Do not tune the scorer in this evaluation-only PR to make these results appear better. Any scorer modification must be a separate, regression-tested proposal and must continue to leave live behavior untouched unless separately authorized.

## Release gate

No live influence is considered unless a held-out, independently reviewed evaluation demonstrates:

- improvement over the unchanged deterministic baseline on relevant fallback cases;
- no material increase in false-positive recommendations or unsupported doorways;
- conservative behavior when both candidates are insufficient;
- results across distinct question classes and genuinely distinct candidate pairs, not only paraphrases of one pair;
- stable behavior under the existing regression, safety, visitor-boundary, and end-to-end suites.

Passing this protocol is not automatic authorization to ship. Any future bounded intervention requires a separate reviewed change, explicit release authorization, and regression testing. Until then, fuzzy relevance remains diagnostic-only.
