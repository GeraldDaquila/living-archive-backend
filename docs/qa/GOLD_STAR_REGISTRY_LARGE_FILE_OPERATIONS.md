# Large canonical Gold Star registry: read, verify, and update

**Authority:** `docs/qa/gold_standard_registry.json` on `main` remains the sole authoritative Gold Star ledger. This runbook changes the transport method, not the registry's authority or governance.

## Verified connector capability

The ordinary GitHub Contents-file retrieval path may return incomplete or empty content for this large JSON file. Do not treat an empty/short Contents response as an empty registry and do not reconstruct the file from snippets.

The connected GitHub integration exposes the Git Database API operations needed to work with the complete object:

- `fetch_blob(repository_full_name, blob_sha)` — retrieve the complete UTF-8 blob by its SHA.
- `create_blob(repository_full_name, content, encoding="utf-8")` — write a complete replacement blob and obtain its SHA.
- `create_tree(repository_full_name, tree_elements, base_tree_sha)` — create a tree that changes the registry path while preserving every other path from the base tree.
- `create_commit(repository_full_name, message, tree_sha, parent_sha)` — create a commit from the resulting tree.
- `update_ref(repository_full_name, branch_name, sha, force=false, expected_sha=...) ` — advance the working branch with a compare-and-swap guard.

This sequence was verified against the 1.2 MB canonical registry on 2026-11-28. The full blob returned 1,212,623 characters; the Git tree entry reported the registry blob as 1,213,574 bytes. These are different units and should not be conflated.

## Read protocol

1. Resolve the exact branch/ref and fetch its commit.
2. Fetch that commit's tree and locate the exact path `docs/qa/gold_standard_registry.json`.
3. Record the tree entry's blob SHA, byte size, branch head SHA, and commit SHA.
4. Call `fetch_blob` with that blob SHA. Do not rely on a truncated Contents response.
5. Parse the complete returned text as JSON. Reconcile `registry_id`, `schema_version`, record count, unique `benchmark_id` values, approved status count, runtime-transfer count, response-quality exemplar count, serial allocation, and the `integrity_audit`.
6. If the blob cannot be retrieved or JSON parsing/reconciliation fails, stop. Never infer missing records or counts.

## Write protocol (Git Database API; preferred for this large file)

1. Read the current working branch head and its root tree. Pin both SHAs.
2. Fetch the exact current registry blob by its tree-entry SHA. Parse and validate the complete registry before editing.
3. Make a minimal additive or explicitly authorized edit in memory. Preserve all unrelated records and top-level fields. Reject duplicate benchmark IDs. Recompute every record-derived audit count and reconciliation note; do not hand-wave or guess.
4. Serialize the entire JSON document as UTF-8. Create a new blob with `create_blob`.
5. Create a new tree using the current root tree SHA as `base_tree_sha`, with exactly one replacement entry for the registry path: `{path: "docs/qa/gold_standard_registry.json", mode: "100644", type: "blob", sha: NEW_BLOB_SHA}`. The base tree preserves all untouched files.
6. Create a commit whose parent is the pinned branch-head commit and whose tree is the new tree.
7. Advance only the working branch with `update_ref(force=false, expected_sha=PINNED_BRANCH_HEAD)`. If the expected SHA does not match, stop, re-fetch the branch, and reconcile the concurrent change. Never force-push over a changed registry.
8. Re-fetch the new blob by its new SHA and parse it again. Verify record identity, unique IDs, exact record count, audit totals, numbering, and unchanged unrelated records.
9. Open/update the PR and require the repository's registry-contract and focused regression checks. Merge only after review and all required gates pass.

## Concurrency and safety rules

- Never issue concurrent writes to the same registry path.
- Never use a stale blob SHA or branch head.
- Never use `force=true` to bypass a registry conflict.
- Never update the canonical JSON from a partial Contents response.
- Never split the authoritative registry into multiple ledgers or create a parallel source of truth to work around transport size.
- Keep the human-readable companion `docs/qa/GOLD_STANDARD_REGISTRY.md` reconciled in the same PR.
- Keep fixtures and screenshots as evidence, not alternate registries.
- Do not allocate a Gold Star serial unless explicitly authorized and all numbering rules are satisfied.
- A standalone response-quality exemplar must retain its explicit non-runtime authority boundaries; approval does not establish provider provenance, active runtime transfer, or measured visitor improvement.

## Fallbacks

- For small files, the ordinary Contents API helpers remain convenient.
- For this canonical registry, prefer blob/tree/commit/ref operations.
- Line-range reads are useful for inspection only; they are not a safe replacement for retrieving and validating the complete JSON before a mutation.
- If the blob API itself fails, stop and use an authenticated Git checkout or a separately approved repository-native workflow. Do not silently switch to an incomplete mirror.

## Verified baseline and maintenance record

On 2026-11-28, the canonical registry on `main` was retrieved through `fetch_blob` using the blob SHA from the Git tree. The complete JSON parsed successfully with 200 records, 159 approved Gold Stars, 139 active quality contributors, 18 approved response-quality exemplars, and zero duplicate benchmark IDs. The subsequent PR candidate adds one separately approved standalone exemplar and must be validated against its exact commit before merge.
