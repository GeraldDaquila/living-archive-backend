# FSD Episode-Based Instrument v1 — Design Proposal

Status: proposed candidate design; not activated and not a validated instrument.

## 1. Purpose and boundary

The FSD observes one bounded consequential episode within one explicitly selected system boundary. It examines whether the episode provides evidence for the two canonical transitions:

- Q001 Correspondence: consequential experience meaningfully influences understanding.
- Q002 Correctability: revised understanding meaningfully influences subsequent decision or action, when a warranted and meaningful response is available.

The result describes the observed episode and the respondent's account. One episode cannot establish a stable trait, general system capacity, institutional performance, or a population-level pattern.

## 2. Framing shown before the questions

"Choose one real event or decision in the selected system that produced a meaningful consequence and challenged, tested, or confirmed an existing understanding. Answer only what you know. You may select 'not known' or 'not enough evidence'. Do not include names, identifying details, confidential information, or details that could expose another person. Your answers are used to prepare this report and are not saved as a diagnostic history."

The experience need not result in change. The diagnostic must not assume that change was warranted.

## 3. Proposed structured question sequence

All responses are structured selections, with optional short text only where explicitly indicated. Text limits are enforced server-side. No open-ended narrative is required in v1.

1. **System boundary** — Self; Relationship; Community; Institution; Civilization. The respondent identifies the system being examined, not their own identity.
2. **Prior understanding** — What best describes the understanding or assumption that guided the system before this episode? Options: clearly identifiable; partly identifiable; disputed within the system; not known. Optional neutral description, max 240 characters.
3. **Consequential experience** — What happened that tested or challenged that understanding? Options: observed outcome; direct feedback from affected people; documented evidence; repeated pattern; unexpected consequence; other / not clear. Optional description, max 360 characters.
4. **Consequence significance** — How consequential was this experience for the selected system? Options: materially affected an outcome or decision; exposed a material risk or mismatch; limited or ambiguous consequence; significance not yet clear.
5. **Understanding after the experience** — What happened to the prior understanding? Options: meaningfully revised; qualified or narrowed; examined and retained for stated reasons; not meaningfully reconsidered; no opportunity to reconsider; not known.
6. **Basis for reconsideration** — What best describes the relationship between the experience and any reconsideration? Options: the experience directly changed the explanation; it prompted examination but did not settle the question; it was considered alongside competing evidence; no clear connection; not known.
7. **Subsequent response** — What happened after the understanding was reconsidered? Options: a consequential decision or action changed; a response was tested or piloted; a decision was paused pending evidence; no consequential response followed; response was attempted but blocked; too early / not known.
8. **Understanding-to-action connection** — If a response occurred, how was it related to the reconsidered understanding? Options: directly informed by it; partly informed by it; unrelated or unclear; no response / not known.
9. **Meaningful capacity to respond** — At the relevant time, was a meaningful response reasonably available to the system? Options: yes; partly; no; not known.
10. **Reason for non-change or delay** — If no consequential response followed, what best explains this? Options: evidence did not warrant change; more evidence was needed; authority or resources were unavailable; competing responsibilities or risks; resistance or existing arrangements constrained response; insufficient time has passed; no clear explanation; not applicable.

The UI should show conditional follow-ups only where needed. A respondent must be able to complete the instrument using structured choices without supplying free text.

## 4. Interpretation rules

### Correspondence

- Evidence of a reported Correspondence transition requires a consequential experience (Q3-Q4) and a meaningful reconsideration of the prior understanding (Q5), with a plausible relationship between them (Q6).
- A claim that the understanding changed is respondent-reported unless independently corroborated.
- "Retained after examination" is not automatically failure. It may indicate appropriate judgment if the evidence did not warrant revision.
- "Not known", "no opportunity", ambiguous significance, or missing links must produce insufficient evidence, not a negative score.

### Correctability

- Evidence of a reported Correctability transition requires a reconsidered understanding (Q5-Q6), a subsequent response (Q7), and a plausible link between the understanding and response (Q8).
- A lack of response is not evidence of failure where meaningful authority, resources, time, or opportunity were absent (Q9-Q10).
- A blocked response is evidence of a constraint in the observed episode, not proof of a permanent system incapacity.
- A decision to pause or not change may be appropriate where evidence is incomplete or change is not warranted.

### Overall episode result

The report may describe: both transitions reported; Correspondence reported but Correctability not demonstrated; Correctability cannot be assessed because Correspondence was not established; neither transition demonstrated in this episode; or insufficient evidence. "Not demonstrated" must never be rewritten as "incapable". Prior understanding marked unknown must produce insufficient evidence for Correspondence.

Any generated strengths or enabling conditions must be directly supported by the structured selections. The report must return an empty list when no such condition is evidenced; it must not invent strengths from the mere presence of feedback, documentation, or a subsequent action. Suggested next steps must be clearly framed as suggestions, not as events or outcomes that already occurred.

No numeric capacity score, ranking, pass/fail label, psychometric claim, causal certainty, or stable system diagnosis is permitted.

## 5. Evidence and retrieval boundary

Keep two evidence classes separate:

1. **Episode account:** the respondent's structured answers. These are self-reported and are not independently verified by archive retrieval.
2. **Archive references:** canonical Living Archive sources retrieved to explain the concepts and offer further orientation. These sources are not evidence that the reported episode occurred and must not be cited as corroboration of the respondent's claims.

The backend must not require a minimum of one archive reference per quantum as if that proved the episode. It may show relevant archive references as conceptual context, with their role clearly labeled. Report evidence labels must distinguish "reported by respondent" from "Living Archive reference".

## 6. Privacy and safety

- No names, exact locations, identifying details, case files, or confidential documents requested.
- Optional text is minimized, length-limited, and visibly discouraged from containing personal or confidential details.
- Do not persist raw answers, report text, or diagnostic history by default.
- Do not include raw answers in application logs, error telemetry, analytics, or provider diagnostics.
- The interface must disclose that the submitted structured answers are processed to generate the report and identify the relevant processing/retention terms before launch.
- A future save/export feature, if any, must be a separate explicit action and separately reviewed.

## 7. Implementation sequence

1. Confirm this episode structure against the canonical FSD architecture and editorial intent.
2. Update the request contract to accept a versioned episode payload and validate conditional fields, enums, text bounds, and scale.
3. Replace the legacy ten-item tendency questionnaire only in the draft candidate UI; do not edit the published page until the candidate passes review.
4. Separate episode claims from archive references in the report schema and prompt.
5. Add unit tests for all transition combinations, insufficient evidence, non-change justified by evidence, unavailable response capacity, and no-inference boundaries.
6. Run full regression matrix, then test WordPress proxy → primary → mirror with synthetic non-personal fixtures.
7. Only after review and release approval, stage the page and proxy integration.

## 8. Explicit non-goals

This is not a psychometric instrument, clinical assessment, personnel evaluation, compliance certification, institutional ranking, or a method for diagnosing a person's character. It does not establish a stable system property from one episode. Repeated and sufficiently varied episodes, with independent evidence and an appropriate research design, would be required for broader claims.
