# Decision-rights candidate-set independent review protocol

## Purpose

Independently validate the relevance labels and conditional-activation rules in
`decision_rights_candidate_set_benchmark.json`. This protocol is separate from
runtime retrieval, provider adjudication, semantic application, and answer-quality
validation.

The existing benchmark labels are technical-steward selections. Until the
procedure below is completed and its results are recorded, they are provisional
benchmark governance labels, not independent ground truth.

## Review unit

Review each query against the complete inventory of approved, runtime-active
Gold Star transferable disciplines available at the benchmark revision. Do not
limit review to the six currently nominated candidates: doing so would make
recall outside that nominated set impossible to measure.

For each query, provide reviewers with:
- the query and only the context needed to interpret it;
- each eligible Gold Star's approved question, known theme, reasoning family,
  transferable discipline, qualifying context, and abstention boundary;
- stable anonymized candidate labels for the first-pass review.

Conduct a blinded first-pass review: withhold the steward's expected roles,
current selector output, semantic scores, and other reviewers' labels until
each independent first pass is submitted. Candidate labels are pseudonymous,
but approved question and discipline text must remain visible for meaningful
review; reviewers familiar with the source registry may infer identities. This
is label-blinding, not guaranteed identity-blinding. Reviewers must not consult
the source registry or attempt identity resolution before locking first-pass
annotations.

## Required independent annotations

For every query/candidate pair, each reviewer records one disposition:

- `CORE`: materially contributes to answering the query as asked.
- `CONDITIONAL`: relevant only if a stated condition is present; name the
  observable condition and explain why it is or is not present in this case.
- `RELATED_NOT_NEEDED`: conceptually adjacent but not needed to answer this
  query; must not be counted as a retrieval success.
- `NOT_RELEVANT`: does not materially contribute to this query.
- `INSUFFICIENT_CONTEXT`: the query does not support a defensible relevance
  decision; state the missing information.

Reviewers also record:
1. whether the query itself is answerable or requires abstention/clarification;
2. the minimum set of disciplines needed for an adequate answer;
3. any material candidate omitted from the current steward-selected set;
4. any false-positive risk or cross-domain transfer concern;
5. a concise rationale tied to the actual discipline and its abstention boundary.

A candidate must not be marked CORE merely because it shares vocabulary with
the query or because its discipline is generally valuable.

## Reviewers and adjudication

Obtain two independent first-pass reviews from people who did not author the
steward labels. Reviewers must not confer before submitting their first pass.

Compare results by query and candidate. Record agreement, disagreements, and
the reasons for each disagreement. A third reviewer adjudicates unresolved
differences. Preserve all original annotations; adjudication supplements rather
than overwrites them.

If two independent reviewers cannot establish a stable label, retain the case
as ambiguous or revise its wording. Do not force consensus to preserve the
current benchmark.

## Metrics and reporting

Only independently adjudicated labels may be used as ground truth for quality
metrics. Report separately:

- precision and recall for CORE candidates;
- conditional-candidate precision and activation accuracy;
- related-not-needed false-positive rate;
- abstention/clarification accuracy;
- omitted relevant candidates;
- reviewer agreement and adjudication rate.

Do not collapse CORE, CONDITIONAL, and RELATED_NOT_NEEDED into one positive
class. Do not count a conditional candidate as correct when its trigger is
absent. Report query-level and aggregate results, with the denominator and
candidate inventory revision stated.

The current eight-case fixture may be used as a pilot. Add new paraphrase,
boundary, and negative cases only with independently reviewed labels. Keep a
separate held-out set whose labels are not used to choose selector thresholds,
weights, embeddings, or ranking logic.

## Release boundary

Independent review does not prove runtime retrieval or substantive answer
application. Keep these as separate gates:

1. label validity and benchmark coverage;
2. retrieval performance on held-out cases;
3. substantive application in delivered answers;
4. answer integrity and abstention;
5. release approval.

No selector, threshold, ranking, embedding, prompt, or production behavior
change is authorized by completion of annotation alone. Any proposed runtime
correction must be minimal, separately tested, and compared against the
unchanged baseline. No synthetic traffic may be sent to production for this work.
