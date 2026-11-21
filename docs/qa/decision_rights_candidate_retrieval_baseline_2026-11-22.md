# Decision-rights candidate retrieval baseline — evidence record

## Run identity

- Pull request: #1861
- Branch: `qa/governed-decision-rights-candidate-benchmark`
- Commit: `39e603c8ee7a38a7ab9bcad0b20f4cb39a29b57e`
- Base: `0add856aea30d008e85e96fed551bc73a8ff72b9`
- Real-BGE workflow run: [44942286615](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/44942286615)
- Full-suite inventory run: [44942286655](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/44942286655)

## Interpretation boundary

The eight expected candidate sets remain steward-selected and are explicitly
marked `STEWARD_SELECTED_PENDING_INDEPENDENT_REVIEW`. The figures below are
therefore diagnostic agreement with provisional labels, not independently
validated precision/recall and not proof of actual runtime quality.

The real-BGE workflow passed because the diagnostic executed and reported its
measurements. It does not assert that retrieval quality is adequate.

## Production selector diagnostic

| Case | Precision | Recall | Observed behavior |
|---|---:|---:|---|
| central-question | 0.0000 | 0.0000 | Returned three candidates outside the provisional core set |
| distributed-authority-paraphrase | 0.3333 | 0.3333 | One of three provisional core candidates |
| delegated-authority | 1.0000 | 0.2500 | Returned only conditional #77 |
| formal-informal-mismatch | 1.0000 | 0.5000 | Returned two of four provisional candidates |
| leadership-versus-position | 0.3333 | 1.0000 | Found the provisional expected candidate plus two extras |
| garden-chores-negative | 1.0000 | 1.0000 | Correctly abstained |
| household-chores-negative | 1.0000 | 1.0000 | Correctly abstained |
| underspecified-ambiguity | 1.0000 | 1.0000 | Correctly abstained |

## Counterfactual raw BGE semantic top-three

This ranking is diagnostic only. It bypasses production selector anchor,
threshold, and ambiguity gates; it is not a proposed replacement selector.

| Case | Raw semantic top-three (score) |
|---|---|
| central-question | delegated-judgment #77 (0.7453); actionable ethical responsibility (0.7198); AI staffing judgment (0.6827) |
| distributed-authority-paraphrase | delegated-judgment #77 (0.6688); formal/informal dynamics (0.6649); formal/actual power (0.6630) |
| delegated-authority | delegated-judgment #77 (0.7420); consequential action under uncertainty (0.6510); actionable ethical responsibility (0.6458) |
| formal-informal-mismatch | formal/actual power (0.7106); formal/informal dynamics (0.7101); delegated-judgment #77 (0.6507) |
| leadership-versus-position | leadership versus positional authority (0.8286); governance leadership/management distinction (0.7043); stewardship distinction (0.6628) |

Negative cases also produced nonzero raw semantic rankings, but the production
selector abstained. The underspecified case produced a raw semantic candidate
with a 0.6140 score for proportional accountability; this reinforces why raw
similarity cannot replace query sufficiency and conditional-activation logic.

## Findings supported by this run

1. The current production selector does not return the provisional expected core
   candidate set for the central question.
2. On the distributed-authority case, the raw semantic ranking contains formal/
   actual power and formal/informal dynamics but omits two provisional core
   disciplines.
3. On the central question, raw semantic ranking strongly favors #77 even though
   the provisional benchmark makes #77 conditional rather than default-core.
4. The production selector abstains on the three negative/underspecified cases
   in this small pilot.
5. The raw semantic top-three and production selector outputs differ; raw
   semantic ranking is not equivalent to production behavior.

## Full-suite inventory

The historical inventory workflow completed its reporting wrapper, while the
underlying pytest suite exited nonzero:

- 77 failed
- 2,322 passed
- 3 skipped
- 264 subtests passed

This is not a full-suite pass. The failures span multiple pre-existing subsystem
contracts and registry expectations. This run alone does not establish which
failures are regressions relative to the base commit; baseline comparison and
failure-by-failure ownership are required before attributing them to this PR.

## Next gate

1. Obtain independent blinded labels across the complete approved, runtime-active
   Gold Star inventory, using the review protocol.
2. Freeze a held-out set before any selector tuning.
3. Compare unchanged production lexical selection, raw semantic ranking, and
   any proposed hybrid against independently adjudicated labels.
4. Keep retrieval, semantic application, answer integrity, and release approval
   as separate gates.

No runtime code, selector threshold, ranking, embedding, or prompt was changed
for this evidence record. No production traffic or deployment was performed.
