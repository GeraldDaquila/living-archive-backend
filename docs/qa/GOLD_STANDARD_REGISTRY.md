# Living Archive Gold-Standard Registry

**Status:** Initial recovery inventory — incomplete  
**Authority:** Git-tracked source of truth. Render QA should execute a pinned registry revision and publish reports, not serve as the sole authority.  
**Rule:** A question is not an approved gold standard merely because it was tested once. Preserve exact approved text when available; otherwise mark it NEEDS_SOURCE_RECOVERY. Never reconstruct missing approved wording from memory.

## Operating rules
- Keep this registry version-controlled in the living-archive-backend repository.
- Preserve protected use_core.py unchanged.
- Keep General Purpose USE / The Guide and HRN benchmarks structurally separate.
- Preserve exact question, approved response, canonical destination, assertions, provenance, and approval state.
- Keep answer composition separate from destination recommendation.
- Distinguish unit/contract tests, direct API checks, and real browser E2E.
- Every QA report should record registry revision and application commit/runtime.
- Do not weaken an approved benchmark to accommodate a regression.

## Status definitions
- FROZEN_CONFIRMED: saved source explicitly identifies a frozen/approved benchmark; exact text must still be linked where noted.
- CONFIRMED_CASE: scenario and expected behavior documented, but not necessarily an immutable verbatim answer.
- NEEDS_SOURCE_RECOVERY: exact approved wording, complete answer, or original calibration record not yet recovered.
- CANDIDATE: no evidence yet of formal approval.

## A. General Purpose USE / The Guide

### GS-GUIDE-001 — Frozen stewardship composition
- **Status:** FROZEN_CONFIRMED
- **Exact question:** “What is stewardship and why does it matter now more than ever?”
- **Expected contract:** Frozen three-paragraph composition, recorded as 861 characters in the October 2026 handoff. Answer and destination remain distinct.
- **Canonical recommendation:** Foundational Stewardship Cases — https://geralddaquila.com/level-1-case-catalog/
- **Assertions:** Preserve approved composition; separate recommendation; no unexplained direct page handoff.
- **Source:** Saved handoff Pasted text(20261015-000853).txt; historical live E2E https://github.com/GeraldDaquila/living-archive-backend/actions/runs/38645881872
- **Recovery needed:** Retrieve exact frozen answer from repository fixture or authoritative QA record before storing verbatim text here.

### GS-GUIDE-002 — Stewardship explanation without immediate navigation
- **Status:** FROZEN_CONFIRMED
- **Exact question:** “Explain stewardship, but do not send me to another page yet.”
- **Expected contract:** Three paragraphs: (1) stewardship as care for something entrusted to you, with everyday examples; (2) how ordinary choices accumulate and preserve trust/future possibilities; (3) the boundary between stewardship and controlling everything or sacrificing yourself for everyone else.
- **Canonical recommendation:** The Stewardship Age — https://geralddaquila.com/2026/08/19/the-stewardship-age-why-stewardship-will-define-the-twenty-first-century/
- **Assertions:** Answer first; recommendation remains separate; do not rewrite the frozen benchmark.
- **Source:** Saved handoff Pasted text(20261014-185650).txt.
- **Recovery needed:** Retrieve exact approved response text before treating this as a verbatim fixture.

### GS-GUIDE-003 — Reciprocity in the Living Archive
- **Status:** FROZEN_CONFIRMED; fixture referenced in a historical open PR
- **Exact question:** “What does reciprocity mean in the Living Archive?”
- **Expected contract:** Mutual response and neighbors helping, with a clear boundary against coercion or treating help as a debt ledger.
- **Fixture pointer:** tests/fixtures/general_guide_reciprocity_gold_standard.json
- **Test pointer:** tests/test_general_guide_reciprocity_gold_standard.py
- **Historical source:** PR #701 https://github.com/GeraldDaquila/living-archive-backend/pull/701
- **Caution:** Verify current main contains this fixture; do not assume the historical PR was merged.

### GS-GUIDE-004 — Institutional responsibility discovery
- **Status:** CONFIRMED_CASE
- **Exact question:** “Where can I find material about institutional responsibility?”
- **Expected destination in one historical test:** Institutional Stewardship Case Library — https://geralddaquila.com/institutional-stewardship-case-library/
- **Expected behavior:** Substantive discovery grounded in verified content about incentives, governance structures, cultural norms, feedback loops, and institutional memory.
- **Source:** Saved handoff Pasted text(20261014-185650).txt; historical primary/mirror parity recorded.

### GS-GUIDE-005 — Public accountability discovery
- **Status:** CONFIRMED_CASE
- **Exact question:** “Where can I find resources about public accountability?”
- **Expected destination:** Governance & Decentralization — https://geralddaquila.com/2026/05/20/governance-decentralization/
- **Expected behavior:** Explain relevance using verified content about shared goals, conflict resolution, resource allocation, and accountability.
- **Source:** Saved handoff Pasted text(20261014-185650).txt; historical primary/mirror parity recorded.

### GS-GUIDE-006 — Newcomer seeking healthier communities
- **Status:** CONFIRMED_CASE; prior PR browser acceptance recorded, current release status must be checked separately
- **Exact question:** “I'm new to the Living Archive. I care about healthier communities, but I don't know its vocabulary or where to begin.”
- **Expected recommendation:** What Healthy Communities Actually Look Like — https://geralddaquila.com/2025/10/07/t4-codex-overflow-communities-governance-by-resonance/
- **Expected behavior:** Accessible everyday language, relevance explained, actual clickable canonical recommendation; no unexplained direct handoff.
- **Historical evidence:** PR #799, branch fix/guide-fast-healthy-community-canonical-verification; workflow run 39865400687 recorded browser acceptance on the PR head. This does not establish merge or deployment.
- **Source:** Saved project handoff dated October 22, 2026.

### GS-GUIDE-007 — Institutional responsibility / Stewardship Readiness
- **Status:** CONFIRMED_CASE; historical destination conflict unresolved
- **Exact question:** “Where can I find material about institutional responsibility?”
- **Expected destination in another historical test:** Stewardship Readiness — https://geralddaquila.com/stewardship-readiness/
- **Source:** Saved handoff Pasted text(20261015-000853).txt.
- **Important:** Historical records specify different destinations for the same question. Do not collapse them or silently choose one. Recover current approved routing policy and provenance first.

## B. Human Relational Navigator (HRN)

### GS-HRN-001 — Recurring argument / shared contribution
- **Status:** CONFIRMED_CASE
- **Exact question:** “I keep having the same argument with someone I care about, but I’m not sure whether the problem is really between us or something I’m bringing into it.”
- **Expected Round 1:** Humane and perceptive but restrained; open exploration instead of concluding what the relationship means; no premature synthesis or junction; ask a genuine follow-up question; no diagnostic or machine-like language; no premature decision framing.
- **Boundary:** HRN remains structurally isolated from General Purpose USE.
- **Source:** Saved HRN calibration handoff Pasted markdown(20261007-185805).md.

### GS-HRN-002 — Uneven effort in friendship
- **Status:** NEEDS_SOURCE_RECOVERY
- **Exact question:** “I often feel like I am the one making the effort in a friendship, but I do not want to judge my friend unfairly. Can you help me understand this?”
- **Historical outcome:** Prior live endpoint attempt returned application-level composition_unavailable / 503. This is a failure reproduction, not an approved answer.
- **Purpose:** Reliability/recovery case; never label the failure response a gold-standard output.
- **Source:** Saved handoff Pasted text(20261016-013651).txt.

### GS-HRN-003 — Repeated partner argument
- **Status:** NEEDS_SOURCE_RECOVERY
- **Exact question:** “My partner and I keep having the same argument, even though we both say we want things to improve.”
- **Expected dimensions:** Concrete grounding, natural multi-turn continuation, no repetitive question genre, no premature closure; visitor-controlled STOP/CONTINUE only when the relevant junction is earned.
- **Source:** Saved handoff Pasted markdown(20261012-174735).md.
- **Caution:** Calibration sequence reference, not a frozen verbatim answer.

### GS-HRN-004 — Duplicate relational wording in saved notes
- **Status:** NEEDS_SOURCE_RECOVERY
- **Exact question:** “I keep having the same argument with someone I care about, but I’m not sure whether the problem is really between us or something I’m bringing into it.”
- **Purpose:** Routing and Round 1 calibration.
- **Source:** Saved HRN handoff dated October 7, 2026.
- **Caution:** Wording duplicates GS-HRN-001 in the recovered notes. Reconcile whether it is one benchmark with multiple test contexts before deduplicating.

## C. Relevance, fuzzy matching, and navigation

### GS-REL-001 — Disagreement without loss of trust
- **Status:** CONFIRMED_CASE
- **Exact question:** “How can a group hold disagreement without losing trust?”
- **Expected behavior:** Evidence-grounded doors; prefer distinct canonical works over alternate formats of the same work; exclude generic governance-only and unrelated assets; validate canonical URLs.
- **Source:** Saved handoff Pasted text(20261013-012325).txt, Catalogue M0.15.65–M0.15.67 recovery notes.

### GS-REL-002 — Disagreement about what is worth protecting
- **Status:** NEEDS_SOURCE_RECOVERY
- **Exact question:** “What does stewardship look like when people disagree about what is worth protecting?”
- **Expected behavior:** Test actual disagreement/protection intent rather than shallow keyword overlap.
- **Source:** Earlier saved calibration references; original approved record not yet recovered.

### GS-REL-003 — Responsibility versus carrying everything
- **Status:** NEEDS_SOURCE_RECOVERY
- **Known theme only:** Responsibility versus carrying everything. Exact question and approved outcome must be recovered.

### GS-REL-004 — Helping versus taking over
- **Status:** NEEDS_SOURCE_RECOVERY
- **Known theme only:** Helping versus taking over. Exact question and approved outcome must be recovered.

### GS-REL-005 — Sharing responsibility under strain
- **Status:** NEEDS_SOURCE_RECOVERY
- **Known theme only:** Sharing responsibility under strain. Exact question and approved outcome must be recovered.

### GS-REL-006 — Finding the right starting point
- **Status:** NEEDS_SOURCE_RECOVERY
- **Known theme only:** Finding the right starting point. Exact question and approved outcome must be recovered.

### GS-REL-007 — Accountability, transparency, and repair
- **Status:** NEEDS_SOURCE_RECOVERY
- **Known theme only:** Accountability as Responsibility, Transparency, and Repair. Exact question and approved outcome must be recovered.

## D. Cross-system contracts (not counted as answer gold standards)

- Primary/mirror runtime identity and behavioral parity.
- Guide SSE final response envelope preservation.
- Clarification boundary.
- Exactly one API request per click, rendered clickable recommendation, and Ask Another Question reset behavior.
- Guide-to-HRN specialist routing and actual visitor-facing round trip.
- HRN multi-turn continuation, earned junction, STOP and CONTINUE behavior.
- Specialist boundaries between HRN, Formation, Catalogue, safety, LAN, and General Purpose USE.
- Canonical evidence grounding and response-to-destination pairing.
- Provider-exhaustion fault injection. Historical notes caution that a workflow claiming all providers down did not actually force all providers down.

## E. Recovery backlog

1. Search repository fixtures, accepted calibration screenshots, ratings, handoffs, and exact approved answer text.
2. Recover the user-referenced additional 20-or-so examples. Do not invent missing entries from topic labels.
3. Link every record to exact source and preserve approval date/provenance where available.
4. Resolve the two historical destinations recorded for institutional responsibility.
5. Verify whether the reciprocity fixture from PR #701 exists on current main; do not merge an old PR merely to retrieve it.
6. Convert only recovered, approved records into machine-readable fixtures; add automated checks without changing application behavior.
7. Include registry revision/hash in QA reports and preserve the existing E2E infrastructure.
8. Only after inventory reconciliation, decide how the standalone QA Render service should consume a pinned registry revision. Do not use Render's ephemeral filesystem as the sole source of truth.

**Current inventory:** 17 numbered entries, but several are themes/placeholders, duplicates, or contract checks. This is intentionally not represented as a recovered set of 20+ fully validated gold standards.


## F. Exact approved response recovered from authoritative repository fixtures

### GS-GUIDE-002 — exact frozen response (recovered)
- **Authoritative fixture:** `tests/fixtures/general_guide_stewardship_gold_standard.json` on main
- **Fixture SHA:** `7a11e93a4688806704e3f7b388c87128cec917e0`
- **Benchmark ID:** `general-guide-stewardship-gold-standard-2026-10-14`
- **Status in source:** `FROZEN_REFERENCE_ONLY`
- **Exact approved response:**

> Stewardship means taking care of something entrusted to you—such as your time, relationships, shared spaces, money, or the natural world—rather than treating it as if only your immediate needs matter. In everyday life, it shows up in small choices: keeping a promise, maintaining what others rely on, using resources thoughtfully, and considering how your decisions affect people around you.
>
> It matters because ordinary choices accumulate. Carelessness can pass costs to other people or to the future, while responsible care helps preserve trust, usefulness, and possibilities for those who come after us.
>
> Stewardship does not mean controlling everything or sacrificing yourself for everyone else. It means recognizing what is yours to care for, acting responsibly within your limits, and leaving things no worse—and where possible better—than you found them.

- **Expected doorway title:** The Stewardship Age
- **Freeze invariants:** Answer complete before optional doorway; exactly three connected paragraphs; everyday language; no unsolicited taxonomy/list; separate optional doorway; explicit “do not send me to another page yet” forbids direct handoff; one submission renders the answer.
- **Source:** https://github.com/GeraldDaquila/living-archive-backend/blob/main/tests/fixtures/general_guide_stewardship_gold_standard.json

### GS-GUIDE-008 — exact frozen reciprocity response (recovered from PR branch; not on main)
- **Authoritative fixture branch:** `qa/freeze-reciprocity-gold-standard`
- **Fixture:** `tests/fixtures/general_guide_reciprocity_gold_standard.json`
- **Benchmark ID:** `general-guide-reciprocity-gold-standard-2026-10-19`
- **Status in source:** `FROZEN_REFERENCE_ONLY`
- **Exact approved response:**

> Reciprocity means a relationship of mutual response: people give, receive, and support one another over time. It is not a strict tally in which every act must be repaid immediately or in exactly equal measure. For the Living Archive context, this is a useful starting definition; the linked Archive source may offer a more specific framing.
>
> For example, neighbors might take turns checking on an older resident or helping each other with errands. One person may give more during a difficult week and receive help later; the relationship can remain reciprocal without every exchange being identical.
>
> Reciprocity should not be used to demand access, obedience, or repayment from someone who cannot freely offer it. Mutual support works best when contributions respond to real circumstances rather than becoming a debt ledger.

- **Expected doorway title:** Reciprocity Before Bureaucracy: How Communities Coordinated Without Modern Institutions
- **Freeze invariants:** Three connected paragraphs; plain meaning, everyday neighbor example, boundary against coercion/debt-ledger thinking; answer does not claim sole canonical definition; doorway separate and optional; one submission renders substantive answer; must remain useful during provider-bank exhaustion.
- **Important:** PR #701 remains open/unmerged according to the current GitHub record. The fixture is recoverable from its branch, but is not currently present on main. Do not assume it is part of the production test suite until merged or otherwise deliberately incorporated.
- **Source:** https://github.com/GeraldDaquila/living-archive-backend/pull/701

## G. Existing machine-readable relevance evaluation suites discovered on main

These are useful reference material, but they are **additive evaluation fixtures**, not frozen visitor-approved response standards. Their labels are authored expectations; they are not independent human ground truth. Keep that limitation in reports.

| Fixture | Recorded cases | Classification |
|---|---:|---|
| `tests/fixtures/guide_fuzzy_relevance_balanced_evaluation.json` | 4 | Direct / adjacent / unsuitable resource comparison |
| `tests/fixtures/guide_fuzzy_relevance_heldout_paraphrases.json` | 4 | Held-out paraphrases and hard distractors |
| `tests/fixtures/guide_fuzzy_relevance_independent_challenge_set.json` | 16 | Expanded challenge cases; includes correlated paraphrase family and underspecified candidate-set caveats |
| `tests/fixtures/guide_fuzzy_relevance_simulated_question_battery.json` | 10 | Simulated question battery with plausible hard distractors |
| `tests/fixtures/fuzzy_fallback_replay_simulated_cases.json` | 9 | Simulated diagnostic-only fallback replay |

**Count caution:** The four relevance fixtures contain 34 case records in total, but this is not 34 independently validated gold standards. Some cases are correlated, some are simulated, and the independent challenge fixture explicitly records cases where the candidate set is underspecified. The registry must preserve these caveats rather than reporting a misleading pass rate.

### Relevance fixture source references
- Balanced evaluation: https://github.com/GeraldDaquila/living-archive-backend/blob/main/tests/fixtures/guide_fuzzy_relevance_balanced_evaluation.json
- Held-out paraphrases: https://github.com/GeraldDaquila/living-archive-backend/blob/main/tests/fixtures/guide_fuzzy_relevance_heldout_paraphrases.json
- Independent challenge set: https://github.com/GeraldDaquila/living-archive-backend/blob/main/tests/fixtures/guide_fuzzy_relevance_independent_challenge_set.json
- Simulated question battery: https://github.com/GeraldDaquila/living-archive-backend/blob/main/tests/fixtures/guide_fuzzy_relevance_simulated_question_battery.json
- Fallback replay: https://github.com/GeraldDaquila/living-archive-backend/blob/main/tests/fixtures/fuzzy_fallback_replay_simulated_cases.json

## H. Newly verified recovery findings

1. The exact frozen stewardship answer is now recovered from the authoritative fixture on `main`; the earlier inventory no longer needs to leave its response text unresolved.
2. The exact reciprocity response is recoverable from the branch for PR #701, but the PR is still open/unmerged and its fixture is not present on `main`.
3. The existing repository already contains relevance suites beyond the saved ten-question calibration list. They should be indexed, not relabeled as visitor-approved gold standards.
4. The ten-question list recovered from the September 20 handoff remains a calibration question set. Its original approved answers/ratings have not yet been recovered.
5. Next source-recovery pass: inspect the frozen stewardship test and other fixture/test files on `main`, enumerate all relevant QA/fixtures directories, and search saved calibration screenshots/handoffs for the remaining user-referenced approved examples. No Render or production change is warranted at this stage.
