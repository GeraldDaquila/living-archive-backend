# LAN live subject-relevance failure — 2026-10-15

## Status

**Confirmed live defect. No production files were modified.** This report records a read-only visitor-equivalent request against the active Living Archive Navigator REST endpoint.

## Live request

Endpoint: `POST https://geralddaquila.com/wp-json/living-archive/v1/navigate`

Request fields:
- `version: 0.3.1`
- `choice: understanding`
- `situation: Where can I find material about institutional responsibility?`
- `possibility: I want to understand what institutional responsibility means and where the Archive explores it.`
- `clarification: `

HTTP result: **200**

LAN response version: `0.3.3`

The engine returned these three selected destinations:
1. `How Do I Know What I Really Want?` — `/how-do-i-know-what-i-really-want/`
2. `Reference & Notes` — `/about-2/`
3. `GESARA Nodes` — `/gesara-nodes/`

These do not establish a useful destination for the visitor's stated subject, institutional responsibility. The response also used generic reasons rather than showing a grounded relationship to that subject. This is a relevance failure despite a successful HTTP response.

## Source identity verified

The live file `includes/class-lan-engine.php` was read through the authenticated Cowboy MCP file interface and compared byte-for-byte with the recovery branch snapshot. Both were 51,982 characters and matched exactly. This means the code reviewed in this snapshot is the same engine source that produced the live result. It does **not** mean the missing corpus and retrieval index have been recovered.

## Root cause in the current engine

The source has several structural gaps that permit unrelated resources to survive:

- `retrieve()` uses lexical postings and drops high-document-frequency terms, but does not apply a final hard subject-relevance gate to the remaining candidates.
- `anchor_score()` includes the overall lexical score. Consequently, a candidate can exceed the later score threshold without having direct subject terms in its title, excerpt, or categories.
- `plan_quality_issues()` checks exactly three destinations, candidate-set membership, an anchor-score threshold, distinct titles, and role diversity. It does not check whether each destination fits the visitor's subject.
- `deterministic_plan()` applies broad experience/pattern/structure keyword bonuses and selects three items whenever the candidate pool contains at least three eligible resources.
- `navigate()` falls back to that deterministic plan if planning or repair fails, then requires exactly three selected destinations. There is no subject-fit stop condition before visitor-facing output.

These gaps explain how a formally eligible three-door path can still be topically wrong.

## Required structural repair

1. Derive a bounded subject focus from the visitor's own words, separate from generic navigation wording.
2. Preserve raw-query grounding while distinguishing broad lexical score from direct subject evidence.
3. Add a subject-fit gate to the final candidate/plan validation, not just the planner prompt.
4. Apply the same gate to model-selected, repaired, and deterministic fallback plans.
5. If fewer than three genuinely subject-relevant destinations can be established, do not pad the path with unrelated resources. Return a transparent, humane clarification/insufficient-evidence response that the visitor interface can render correctly.
6. Add regression tests for the exact institutional-responsibility question, the existing new-group/dissonance case, open-ended questions, transitions, conceptual inquiries, and the boundary between direct destination requests and broader inquiry.

## Recovery and release boundary

The live corpus and retrieval index still need an approved, auditable export path. A previous range-read probe showed that the static files support HTTP byte ranges, but a bulk recovery attempt was blocked before execution; no bulk export, local recovery artifact, or file-integrity claim is made here.

This branch remains an **archival recovery snapshot, not a deployment candidate**. Do not deploy the LAN snapshot or patch production until the authoritative runtime data and index are recoverable and the subject-fidelity suite passes. The frozen Guide core and HRN are outside this repair.
