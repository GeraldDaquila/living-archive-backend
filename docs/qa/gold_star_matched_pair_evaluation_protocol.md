# Gold Star matched-pair evaluation protocol

## Scope

This protocol measures the incremental effect of **approved cross-question structural guidance** on held-out synthetic questions.

- **Control:** ordinary General Guide composition with the baseline Gold Star v2.0 quality contract intact, but with the active approved cross-question lesson contribution suppressed.
- **Treatment:** the same composition path plus an approved Gold Star lesson and its candidate-bound adjudication contract when guidance is actually retrieved and included in the provider prompt.

This does not compare the Guide with all Gold Star functionality disabled. It isolates the incremental approved lesson-guidance contribution, including its candidate-specific prompt and adjudication contract. A treatment pair is invalid unless at least one approved candidate was exposed in the provider prompt.

## Runtime gate

The endpoint is `POST /api/internal/gold-star-evaluation-pair`. It is deliberately restricted to the exact USE2-Mirror Render service ID and returns 404 unless all of the following are true:

1. `RENDER_SERVICE_ID` equals the hard-coded USE2-Mirror service identity in `gold_star_evaluation_runner.py`.
2. `GOLD_STAR_EVALUATION_ENABLED=true`.
3. `GOLD_STAR_EVALUATION_SECRET` is configured with at least 32 characters.
4. The caller supplies the exact secret in `X-Gold-Star-Evaluation-Key`.

Never configure the evaluation secret or enable flag on Gerald's Workspace-primary. No secret is stored in the repository or GitHub Actions.

## Request contract

The body is a JSON object with exactly three fields. The 1 KB body limit is enforced incrementally while streaming the request, not only after buffering it:

```json
{
  "case_id": "heldout-practical-trust-001",
  "provider": "groq",
  "model": "openai/gpt-oss-120b"
}
```

The case ID must be one of the fixed `held_out` records in `docs/qa/guide_learning_evaluation_set.json`; the allowlist must equal the complete held-out split, including `heldout-community-rule-design-transfer-001`. The caller cannot supply a question, prompt, answer, history, visitor identity, or arbitrary content.

One request generates one pair (two fresh provider generations). The process accepts at most three distinct successful case IDs. The exact provider/model pin is local-only and fail-closed; no sibling model or active-active counterpart is permitted. If the requested model is unavailable, blocked, or fails, the pair is not returned as evidence.

## Output handling and blinding

The response contains:

- `blind_artifacts`: two outputs in randomized order, containing only the case ID, arm-neutral opaque artifact reference, and answer text. No doorway metadata or other ancillary fields are exposed to reviewers.
- `operator_manifest`: private mapping of artifact references to control/treatment, plus provider/runtime/prompt/configuration/registry fingerprints, candidate-exposure metadata, and arm-specific doorway metadata.

The runner randomizes **generation order** for each pair as well as reviewer presentation order, and records the actual control/treatment generation order in the private operator manifest. This reduces systematic order effects and makes each pair auditable; it does not eliminate all provider nondeterminism or guarantee identical generation conditions beyond the recorded pins and fingerprints.

Share only `blind_artifacts` with the reviewer. Keep `operator_manifest` separate until scoring and reviewer verdict are locked. Share no manifest fields, doorway metadata, or operator mapping with the reviewer before the verdict is recorded. The runner returns outputs in memory and does not persist them. The operator must preserve the blind artifacts in a separately controlled location and use those opaque references in the final review record.

The runner records no visitor data, identity, question text, answer text, or session information. It does not write evaluation files, mutate the Gold Star registry, score outputs, or approve lessons.

## Pair validity

A pair is rejected unless:
- Both arms return a fresh provider candidate from the exact pinned provider/model, with the same shared base prompt and common generation configuration. The per-arm response-schema hashes are retained to disclose the treatment-specific adjudication schema.
- Control receives zero Gold Star candidates.
- Treatment has at least one approved candidate and its guidance exposure is `included_in_provider_prompt`.
- Neither arm reuses the composition cache.
- Neither final composer output was replaced by a deterministic response rewrite.
- Runtime commit, composition contract, generation-config fingerprint, provider-schema fingerprints, and registry digest are recorded. The base-prompt fingerprint hashes the complete shared system/user messages with only the treatment-specific lesson instruction excluded; both arms must match exactly. The shared baseline retains the same generic Gold Star integration contract in both arms. The provider composition schema may contain the treatment-specific candidate-adjudication contract; its exact per-arm hash is recorded rather than falsely described as identical.

## Human review

After the blinded outputs have been reviewed, the operator may combine the manifest with the review scores, NA reasons, hard-gate assessments, verdict, evidence reference, and review timestamp required by `gold_star_adaptation_evaluation.py`.

Three distinct case IDs across at least two case families are required before a batch can become eligible for human promotion review. Even then, the evaluator never auto-promotes a lesson; human approval remains mandatory.

## Deployment boundary

This endpoint is dormant in repository code. Do not configure its secret, enable flag, deploy it, or call it before the USE2-Mirror allocation reset on 2026-12-01 and explicit deployment authorization. Both Render services auto-deploy from `main`; merging this PR would trigger the primary deployment and an attempted Mirror build. Keep this PR unmerged until a Mirror-only deployment path is explicitly authorized.
