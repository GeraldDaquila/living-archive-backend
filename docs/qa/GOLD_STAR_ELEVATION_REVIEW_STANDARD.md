# Gold Star Elevation Review Standard

**Status:** Mandatory for every new Gold Star approval  
**Authority:** Canonical Gold Standard Registry and its fail-closed integrity validator  
**Effective:** Upon merge to `main`

## 1. Purpose

Every proposed Gold Star elevation must be classified before approval so that a new learning contribution, an exact-question successor, a paired exemplar, a standalone response-quality exemplar, and a duplicate are never conflated.

The canonical registry remains the authority for approved records and serial numbers. This standard adds a mandatory review gate; it does not authorize automatic approval, record deletion, renumbering, or changes to an existing approved response.

## 2. Required review sequence

Before a proposed record is added with status `USER_APPROVED_GOLD_STANDARD`, the elevation reviewer must:

1. Confirm that the actual response was reviewed and that the user explicitly approved its elevation.
2. Normalize the proposed question using the canonical registry normalization: Unicode punctuation translation for the supported dash and apostrophe variants, whitespace collapse, case-folding, and removal of terminal question/exclamation/full-stop punctuation.
3. Compare the normalized question against every currently approved record.
4. Identify every same-question record and inspect its approval status, runtime authority, response, and explicit lineage links.
5. Assign the correct family classification below. If the evidence does not support one classification, stop the elevation and resolve the ambiguity before approval.
6. Record the review metadata on the proposed registry record.
7. Run the Gold Star integrity validator and question-family audit. A failed or incomplete review blocks merge.

Semantic similarity alone does not merge two questions into one exact-question family. Reviewers may note conceptual relationships in the rationale, but the deterministic family identifier is based only on the normalized exact question.

## 3. Required classifications

| Classification | Use when | Required evidence |
|---|---|---|
| `NEW_QUESTION_FAMILY` | No other approved record has the same normalized question | Exact-question comparison returns no related approved IDs |
| `EXACT_QUERY_SUCCESSOR` | The new record replaces an existing record's exact-query answer authority | Reciprocal `replaces_exact_query_runtime_authority_of` and `runtime_exact_query_successor` references |
| `SUPERSEDED_HISTORICAL_REFERENCE` | The new record is explicitly retained as a historical predecessor/reference | Reciprocal successor and predecessor references; no competing runtime authority |
| `PAIRED_RESPONSE_QUALITY_EXEMPLAR` | The new response is a deliberately paired exemplar for an existing active record | `paired_active_benchmark_id` points to a same-question approved record |
| `STANDALONE_RESPONSE_QUALITY_EXEMPLAR` | The response is independently approved for response quality and does not claim runtime or exact-answer authority | `generation_class=user_approved_response_quality_exemplar`, `standalone_response_quality_exemplar=true`, and no successor, supersession, or paired-record link |

A repeated-question record that cannot satisfy one of these evidence patterns is `REVIEW_REQUIRED` and must not be elevated until resolved. An identical answer body is separately flagged for review; it is not silently accepted as a second contribution.

For a unique question whose record is itself a response-quality exemplar, the family classification is `NEW_QUESTION_FAMILY`; its existing generation-class metadata continues to identify its response-quality-exemplar role.

## 4. Mandatory registry metadata

Every newly approved record must contain a `question_family_review` object:

```json
{
  "question_family_review": {
    "family_id": "qf-<first-16-hex-characters-of-sha256-normalized-question>",
    "classification": "NEW_QUESTION_FAMILY",
    "reviewed_by": "user",
    "reviewed_at": "YYYY-MM-DD",
    "rationale": "Explain why this classification is supported by the registry evidence.",
    "related_benchmark_ids": []
  }
}
```

Rules:

- `family_id` is computed as `qf-` plus the first 16 lowercase hexadecimal characters of SHA-256 over the normalized question encoded as UTF-8.
- `classification` must be one of the five values in Section 3 and must agree with the record's actual links and the current registry.
- `reviewed_by` must be `user`; this is a record of explicit user disposition, not an assistant inference.
- `reviewed_at` uses ISO date format `YYYY-MM-DD`.
- `rationale` must contain at least 20 non-whitespace characters and explain the decision.
- `related_benchmark_ids` must be the complete, sorted list of all other approved records with the same normalized exact question. It must be an empty array for a new family.
- The existing response-review and explicit user-elevation approval fields remain independently required.

## 5. Grandfathering and immutability

Records already approved on canonical `main` when this standard takes effect are grandfathered. Their historical approval evidence is not reconstructed or rewritten merely to satisfy a newly introduced field.

Every approval added after the effective merge is subject to this gate, including a previously existing candidate ID whose status changes to approved.

The review gate does not alter the canonical approved count, active-contributor count, exemplar count, numbering state, or response content. Existing approvals remain immutable under the registry's established policies.

## 6. Enforcement

The following controls are mandatory:

- The Gold Star registry validator invokes the question-family audit in enforcement mode against the fetched canonical `origin/main` baseline.
- The audit fails closed if a new approval lacks its review object, has a mismatched family ID or classification, omits or invents related IDs, lacks explicit user review/elevation approval, or belongs to an unclassified repeated-question family.
- The audit also fails on unclassified existing repeated families or identical approved response bodies.
- Gold Standard Registry Validation CI runs the dedicated regression tests and publishes the JSON family-audit artifact.
- A pull request that fails this gate must not be merged.

## 7. Authority boundary

The family audit is deterministic and read-only. It reports classification and lineage; it does not approve records, infer user consent, rewrite responses, merge records, delete historical evidence, allocate serials, or modify runtime authority.

Only explicit user approval can authorize a new Gold Star elevation. The canonical registry and its existing numbering validator remain authoritative.
