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


## I. Recovered benchmark metadata: compound stewardship explanation

### GS-GUIDE-001 — frozen three-paragraph stewardship answer

- **Exact question:** “What is stewardship and why does it matter now more than ever?”
- **Status:** FROZEN_CONFIRMED; exact 861-character response recovered by byte-for-byte text match against the frozen stewardship fixture and the historical v489.259 deterministic recovery implementation.
- **Frozen response contract:** Three paragraphs, recorded at **861 characters** in the October 15 handoff; answer and recommendation remain separate.
- **Expected destination in the recorded frozen benchmark:** **Foundational Stewardship Cases** — https://geralddaquila.com/level-1-case-catalog/
- **Historical dual-service evidence:** Guide dual-service E2E run [38645881872](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/38645881872) and production validation run [38645881798](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/38645881798) were recorded as successful at v489.259. The handoff records an 861-character response on both services, separate recommendation rendering in the response contract, and destination checks. These are historical results, not proof of current production status.
- **Important destination discrepancy:** The October 15 handoff also notes a Stewardship Readiness destination in a discovery test scenario. Do not treat that as the expected destination for this frozen explanatory benchmark; preserve it as a distinct historical discovery scenario unless further provenance shows otherwise.
- **Recovery result:** The historical v489.259 source at `main.py` lines 3872–3880 contains the exact 861-character, three-paragraph response in its deterministic stewardship recovery branch. The text matches `expected_response` in `tests/fixtures/general_guide_stewardship_gold_standard.json` exactly, including punctuation and paragraph breaks. This independently corroborates the missing answer wording, although the existing fixture's query is the separate “Explain stewardship, but do not send me to another page yet.” benchmark. Preserve that query distinction.
- **Source:** Library handoff `Pasted text(20261015-000853).txt`, section “Frozen General Purpose gold standard” and “E2E infrastructure — verified configuration”; corroborating handoff `Pasted text(20261015-085140).txt`.

### E2E registry rule

The existing workflow `.github/workflows/live-guide-dual-service-e2e.yml` is part of the preserved E2E infrastructure. Registry adoption must add a pinned registry revision/hash to test evidence without replacing the lightweight release-identity gate or dropping visitor-journey checks. A workflow success from October 2026 is historical provenance only; future registry reports must identify the tested application commit, runtime fingerprint, registry revision/hash, exact scenario IDs, and whether the test was API-level or browser-level.


## J. Historical E2E payload recovery result

The historical run was inspected directly rather than inferred from its summary:

- Run [38645881872](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/38645881872), job `116203181984`, completed successfully on October 15, 2026.
- Its decoded job log contains the echoed Python test script and summary lines showing `response_chars=861`, three paragraphs, and the Foundational Stewardship Cases recommendation for both primary and backup.
- The job log does **not** print or preserve the response body. The run exposes no workflow artifacts.
- The separate run [38645881798](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/38645881798) also exposes no workflow artifacts; its job is a broad v487 validation suite, not a response-body archive.
- The current workflow source confirms that the relevant assertions inspect the response in memory and print only length/paragraph/recommendation metadata. It does not write the body to a retained artifact.

**Conclusion:** These historical runs cannot supply a verbatim 861-character answer. They are valid behavioral/provenance evidence, but not a text fixture. Keep GS-GUIDE-001 marked as exact-text recovery pending until an authoritative response body is located. Do not weaken this distinction by using a newly generated response or the separate no-navigation stewardship fixture.


## K. Exact response recovery completed — compound stewardship benchmark

The missing answer text has now been recovered from the historical source tree, rather than reconstructed.

- **Source commit:** `ab561433a984118b18560aa3a8a9ee6203e61de9` (v489.259)
- **Source file and lines:** `main.py`, lines 3872–3880; the deterministic fallback branch returns the response for stewardship definition/explanation queries.
- **Exact text length:** 861 characters, including the two paragraph-separating blank lines.
- **Paragraph count:** 3.
- **Independent exact-match reference:** `tests/fixtures/general_guide_stewardship_gold_standard.json`, blob SHA `7a11e93a4688806704e3f7b388c87128cec917e0`; its `expected_response` is exactly 861 characters and text-identical.
- **Historical benchmark query:** “What is stewardship and why does it matter now more than ever?”
- **Historical destination for this benchmark:** Foundational Stewardship Cases — https://geralddaquila.com/level-1-case-catalog/
- **Important separation:** The same response text is also used in a distinct no-navigation benchmark whose question explicitly forbids immediate navigation and whose expected optional doorway is The Stewardship Age. Text reuse does not make those query contracts interchangeable. Each query retains its own navigation expectation.
- **Confidence:** High for exact answer wording, because the historical deterministic branch and independently frozen fixture are text-identical and match the documented length and paragraph count. The historical run logs still do not expose the actual returned payload, so the logs alone cannot prove which generation path produced that live response. The source match is the strongest available exact recovery evidence.
- **Registry rule:** Future test fixtures should reuse the exact text without editing it. Test the compound query's separate Foundational Stewardship Cases recommendation independently from the no-navigation query's separate The Stewardship Age doorway.


## L. Gold Standards #20 and #21 recovered from accepted-response records

Two additional accepted General Guide response records have been recovered from their exact JSON fixture diffs in open, unmerged PRs and copied into the central machine-readable registry. The response text and acceptance invariants are preserved; neither source PR has been merged by this recovery work.

### GS-GUIDE-020 — practical trust application

- **Question:** “I understand the importance of trust, but what would I actually do differently in an organization trying to live by it?”
- **Recorded rating:** 9/10; recorded as Gold Standard #20 on October 22, 2026.
- **Accepted response:** Preserved verbatim in `docs/qa/gold_standard_registry.json` under benchmark ID `general-guide-practical-trust-application-2026-10-22`.
- **Behavioral invariants:** Concrete, observable organizational actions before a follow-up; accountability and follow-through; check outcomes with affected people; no unsolicited service doorway.
- **Source PR:** [#777](https://github.com/GeraldDaquila/living-archive-backend/pull/777), branch `qa/register-gold-standard-20`, commit `113039181ea810563726e48b77786de789d4aeba`.
- **Source status:** Open/unmerged. The central record is a preserved reference; it does not mean the source PR is part of `main`.

### GS-GUIDE-021 — accountability, trust, and harm repair

- **Question:** “How might accountability, trust, and the ability to repair harm reinforce one another?”
- **Recorded rating:** 9.5/10; recorded as Gold Standard #21 on October 22, 2026.
- **Accepted response:** Preserved verbatim in `docs/qa/gold_standard_registry.json` under benchmark ID `general-guide-conceptual-accountability-trust-harm-repair-2026-10-22`.
- **Behavioral invariants:** Explain the mechanism connecting the concepts; connect responsibility to visible action and trust to observable behavior; explain repair as addressing consequences and changing what allowed harm; do not imply repair erases harm or guarantees trust; no unrequested doorway.
- **Source PR:** [#779](https://github.com/GeraldDaquila/living-archive-backend/pull/779), branch `qa/register-gold-standard-21-conceptual-relationships`, commit `8535fc8343f7bfb45a52eb86fa83964f3729511a`.
- **Source status:** Open/unmerged. The central record is a preserved reference; it does not mean the source PR is part of `main`.

### Registry interpretation

These two records expand the central inventory from four to six machine-readable General Guide records. Their source records explicitly describe accepted live visitor responses and include ratings, but they are behavioral references rather than mandatory templates. Their status remains `FROZEN_REFERENCE_ONLY` in this registry until the registry's source-status model can represent accepted-but-unmerged evidence without conflating it with production-main availability. No application code, WordPress, Render, or production service was changed.


## F. Newly reconciled source artifacts — October 23, 2026

These records were added to `gold_standard_registry.json` from historical PRs and fixture patches. They are deliberately not all classified as approved gold standards.

### Exact historical response recovered; approval evidence still missing

- **Hindsight accountability** — PR #750, merged. Exact question and full deterministic response recovered from `deterministic_answer_recovery.py`. Status: `RECOVERED_HISTORICAL_RESPONSE_PENDING_APPROVAL_EVIDENCE`. No visitor rating/approval record found yet.
  - Question: “If the group made the best decision it could with the information available at the time, how should it distinguish genuine accountability from unfairly blaming people in hindsight?”
  - Source: https://github.com/GeraldDaquila/living-archive-backend/pull/750

### Recovered calibration/regression scenarios; not frozen answer standards

- **Ethical trade-off** — PR #749, merged. Exact question and assertions recovered; full accepted response and approval/rating record remain missing. Question: “What if each person sincerely believes they are protecting something important, but protecting one person's priorities means another person will lose something they deeply value? How should we decide what to protect?”
- **Responsibility boundary** — PR #794, merged. Contract clauses recovered: distinguish personal contribution from system-level accountability; recognize pressure from noticing; connect shared responsibility to authority/resources/obligations; provide a defined contribution and identify what requires others' commitment. Exact original question, complete approved answer, and rating remain missing.
- **Practical collective next step** — PRs #755–#757. One lineage, not three standards. The core query also appears in the relevance evaluation fixture: “If the group agrees that something must change but its members disagree about what to do first, what would be a constructive next step?” The contract requires one low-risk action before optional context and preserves agency. No single approved exact answer/rating recovered.
- **Harm-reduction outcome evaluation** — PRs #763–#766 and #768. One scenario lineage, not five standards. Query: “How can we tell whether a revised approach is genuinely reducing harm?” Must require baseline, observable outcomes, comparison over time, feedback from affected people, and unintended-consequence checks; distinguish this intent from FSD system-pattern diagnosis. Exact accepted recovery answer/rating remains to be recorded.

### Relevance and shadow-evaluation fixtures — not gold-standard answer texts

- **Balanced relevance evaluation** — PR #758, four cases: ethical trade-off, harm repair, collective next step, accountability; each contrasts direct, adjacent, and unsuitable candidates. Labels are authored expectations, not independent ground truth. https://github.com/GeraldDaquila/living-archive-backend/pull/758
- **Held-out paraphrases** — PR #760. Tests paraphrase transfer and topical distractors; exact current case count still to verify. https://github.com/GeraldDaquila/living-archive-backend/pull/760
- **Independent challenge set** — PRs #761–#762. Simulated labels, not independent human ground truth. Three consultation/participation cases share a candidate pair and form one correlated family. Two administrative-procedure cases are marked `candidate_set_underspecified`, so their forced pairwise choice is not valid semantic ground truth. Current main fixture: 4 cases (blob SHA `643fc07bf620d923461373628d1c3441234f702d`). https://github.com/GeraldDaquila/living-archive-backend/pull/762
- **Simulated question battery** — PR #761. Diagnostic direct-versus-adjacent relevance evaluation; not approved answer gold standards. Current main fixture: 10 cases (blob SHA `7a146a44eb8a37f432d0b9e618aede151779e06a`).
- **Fuzzy fallback replay** — PR #762. Simulated diagnostic cases; not approved answer gold standards. Current main fixture: 9 simulated cases (blob SHA `f03afa3157c683479591b67d835065f922ceeab0`).
- **Practical-trust shadow diagnostic** — PR #772. Hypothesis/evaluation-only tests for practical application versus generic inquiry. Keep distinct from approved Gold Standard #20, already recorded as the accepted 9/10 live response.

### Source-lineage rules

- PRs #755–#757 are one evolving practical-next-step defect lineage.
- PRs #763–#768 are one evolving outcome-evaluation routing/composition defect lineage.
- PRs #761–#762 are one evolving fuzzy challenge-set lineage.
- A merged implementation fix does not by itself establish that its test question/answer was visitor-approved.
- Simulated candidate labels and shadow diagnostics must not be counted as approved gold standards.
- The original “20+” gold-standard collection is **still not fully recovered**. Original numbering, several exact questions/answers, and approval/rating records remain open reconciliation items. Do not claim completeness until each original item is linked to source evidence or explicitly classified as missing, duplicate, superseded, simulated, or awaiting approval.


**Verified current fixture counts:** balanced relevance 4; held-out paraphrases 4; independent challenge set 16; simulated question battery 10; fuzzy fallback replay 9. These total 43 fixture cases, but are not 43 approved gold standards. The independent challenge set includes correlated cases and underspecified candidate pairs; simulated cases are not independent human ground truth. The separate ten-question calibration set is also not an approved-answer set.

**Registry size at this revision:** 33 structured records, including the five fuzzy evaluation/diagnostic records and one ten-question calibration-set record. This count describes records, not approved gold-standard answers.


## G. Original 14-standard forensic sequence recovered from Issue #747

Source: [Issue #747 — Forensics: establish provenance of the 14 Guide Gold Standards](https://github.com/GeraldDaquila/living-archive-backend/issues/747). Its comments establish provider/source attribution and include an explicit user-approval record for the deterministic-recovery trade-off answer.

### Exact original prompts recovered

- **Original #1:** “How does responsibility differ from carrying everything yourself?” — successful Groq Qwen composition logged; exact accepted response/rating still missing.
- **Original #2:** “How can I tell when helping has turned into taking over?” — successful Groq Qwen composition logged; exact accepted response/rating still missing.
- **Original #3:** “What does sharing responsibility look like when a team is struggling?” — successful Groq Qwen composition logged; exact accepted response/rating still missing.
- **Original #4:** “Where should I start if I want to understand trust-based systems?” — primary-service logs show a navigation-specialist handoff to Start Here (https://geralddaquila.com/start-here-2/), not a logged General Guide composition event.
- **Original #5:** “What does accountability really mean?” — successful Groq Qwen composition logged; exact accepted response/rating still missing.
- **Original #6:** “Explain a concept that is not directly covered by an available Archive resource” — successful Groq Qwen composition logged; exact accepted response/rating still missing.
- **Original #7:** “What does the Archive specifically say about a claim for which no supporting source is retrieved?” — successful Groq Qwen composition logged; exact accepted response/rating still missing.

### Original #8–#14: numbered slots confirmed; exact prompts still missing

Issue #747 confirms successful Groq Qwen compositions for these seven slots and provides only these topic descriptions, not verbatim questions:

- **#8:** Recurring problems.
- **#9:** Authority without agency.
- **#10:** Formal authority refuses to listen.
- **#11:** Legitimate safeguards versus power protection.
- **#12:** New conditions / moving goalposts.
- **#13:** Genuinely new risk.
- **#14:** Real risk imposing costs on those who accepted the original decision.

Each has a separate recovery placeholder in the JSON registry. The original question wording, exact accepted answer, doorway, visitor rating, and approval record remain unfilled; none have been reconstructed from these topic summaries.

### Explicit approval recovered: deterministic-recovery trade-off

Issue #747 comment [#6322797433](https://github.com/GeraldDaquila/living-archive-backend/issues/747#issuecomment-6322797433) explicitly records user approval on October 22, 2026, of the exact ethical trade-off answer now stored in the JSON registry. The displayed navigation title is “Leadership Case Study 01: Decision-Making Under Pressure and Resource Scarcity.” The numeric rating and destination URL are not stated in that approval record. The comment calls it “Gold Standard #2”; however, the previously recorded reciprocity standard was also described as the second Guide gold standard. Numbering conflict unresolved: preserve both source labels and do not renumber without the original sequence record.

### Attribution and quality limits

The forensic issue attributes #1–#3 and #5–#7, and #8–#14, to successful Groq qwen/qwen3.8-27b composition. #4 is a separate navigation-specialist path. These logs establish source/provider attribution but do not supply every exact accepted output. The next unaccepted edge-case prompt is a provider-bank-exhaustion/deterministic-recovery control, not an accepted gold standard. Do not conflate it with the accepted trade-off response.

The issue also records that query/history hashes are not unique invocation IDs and that the complete exact model inputs/outputs were not captured for every run. No component-by-component causal claim should be treated as proven from provider attribution alone.


### Additional failure-control record

The JSON registry also records the unaccepted provider-exhaustion prompt from Issue #747 as a separate negative reliability control. Its exact prompt and provider-attempt sequence are captured, including the Groq/Workers/OpenRouter timeouts, Groq TPM rejection, and NVIDIA hosted-function 404. The final response was logged as 410 characters, but the exact text was not recovered. This is explicitly not a gold-standard answer and must not be counted as one.
