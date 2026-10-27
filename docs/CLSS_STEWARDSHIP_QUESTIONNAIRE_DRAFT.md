# CLSS Stewardship Coherence Questionnaire — Design Draft

**Status:** Draft for validation against locked governing model in [Issue #998](https://github.com/GeraldDaquila/living-archive-backend/issues/998) and implementation task [Issue #999](https://github.com/GeraldDaquila/living-archive-backend/issues/999).

**This is a design artifact, not a claim that the live WordPress plugin has been updated.** Do not replace the production questionnaire until the draft is reviewed against the acceptance criteria and the current UX.

## Governing question

Where does the exercise of responsibility align with—or depart from—the commitment to serve? What are the consequences for people and work, and what would restore coherence?

## Design rules

- Elicit linked evidence, not disconnected competency ratings.
- Ask for concrete situations, actions, and consequences.
- Distinguish observed facts, documented outcomes, second-hand reports, and interpretation.
- Preserve counterevidence and context; do not lead the visitor toward a negative conclusion.
- Treat unknowns as gaps, never adverse evidence.
- Third-party reflection may assess whether evidence is consistent with stewardship, but must not claim to know private intent or motive.
- No scores, diagnoses, ranking, or automatic suitability decision.
- Every question must support a useful synthesis and an actionable next step.
- Keep the current session-only privacy boundary. No answer transmission or persistence is introduced by this questionnaire draft.

## Proposed questionnaire sequence

### 1. Responsibility and service — Commitment

**Self mode:** What responsibility or decision am I carrying, who is affected by it, and what does serving them require in this situation?

**Third-party mode:** What responsibility or decision is this person being considered for, who will be affected, and what would serving those people require in this situation?

**Purpose:** Establish the real context, affected people, and the service obligation. Do not assume that the visitor's initial definition is complete or correct.

### 2. Concrete episode — Conduct

**Self mode:** Describe one specific situation in which I exercised this responsibility. What did I actually do or decide, and what options did I consider?

**Third-party mode:** Describe one specific situation in which this person exercised a relevant responsibility. What did they actually do or decide, and what options appeared available?

**Evidence prompts:** What happened, when and in what context? What did you directly observe? What is documented? What did someone else report? What part is your interpretation?

**Purpose:** Ground reflection in an episode rather than reputation, labels, or generalized impressions.

### 3. Consequences for others — Consequences

**Self mode:** What effects did my actions have on the people affected and on the work? What effects might I not have intended or noticed?

**Third-party mode:** What effects did the person's actions have on the people affected and on the work? Which effects were directly observed, documented, or reported?

**Purpose:** Connect conduct to consequences. Ask about agency, clarity, trust, participation, capability, fairness, and work outcomes only where relevant to the example; do not force every category into every case.

### 4. Commitment–conduct comparison — Coherence

**Self mode:** Where did my actions match the responsibility I intended to carry, and where did they fall short? What in the example supports each part of that view?

**Third-party mode:** Based on the available evidence, where did this person's actions align with the responsibility the role requires, and where might they have departed from it? What supports each interpretation?

**Purpose:** Make the central comparison explicit. In third-party mode, assess observable alignment with the role's service obligations—not the person's unknowable inner commitment.

### 5. Challenge, feedback, and accountability — Accountability

**Self mode:** When the effects or concerns were brought to my attention, how did I respond? What did I listen to, contest, acknowledge, repair, or change?

**Third-party mode:** When this person was challenged or given feedback about the situation, what did they do next? What evidence shows listening, clarification, responsibility, repair, avoidance, or continued behavior?

**Purpose:** Examine response to contrary evidence and follow-through. A single event is not automatically a stable pattern; repeated events and repair matter.

### 6. Counterevidence and context — Interpretation check

**Self mode:** What is the strongest evidence that complicates my current interpretation? What situational constraint or alternative explanation should I consider, and what evidence would distinguish it?

**Third-party mode:** What is the strongest evidence against my current interpretation? What context or alternative explanation could account for the behavior, and what additional evidence would distinguish the possibilities?

**Purpose:** Prevent confirmation bias without diluting a well-supported concern. Counterevidence is examined, not used automatically to cancel a real pattern.

### 7. Correction and observable change — Correction

**Self mode:** What specific action, repair, or change would better align my conduct with the responsibility to serve? What support or boundary do I need, and what observable sign would show progress?

**Third-party mode:** What specific behavior, process, support, or boundary would help bring the exercise of this responsibility into better alignment with its service obligations? What observable change would show progress?

**Purpose:** Turn insight into agency. The response should identify who can take the next step and how progress could be observed, without presuming that a conclusion has already been reached.

### 8. Most consequential unknown — Evidence gap

**Self mode:** What important fact remains unknown, and what is the fairest practical way to learn it before I act?

**Third-party mode:** What important fact remains unknown, who has relevant first-hand knowledge, and how can it be checked fairly without treating absence of information as evidence against the person?

**Purpose:** Identify the next inquiry that could most change the interpretation or decision.

## Evidence representation for synthesis

Each response should be represented as a structured evidence item. This is a conceptual schema; field names can be adapted to the existing implementation without changing meaning.

| Field | Meaning |
|---|---|
| `prompt_id` | Stable ID for the questionnaire prompt |
| `dimension` | Commitment, conduct, consequences, coherence, accountability, counterevidence, correction, or unknown |
| `response_text` | Visitor's actual answer, unaltered for provenance |
| `source_type` | First-hand observation, document/outcome, second-hand report, interpretation, or unknown |
| `context` | Relevant conditions and constraints stated by the visitor |
| `affected_parties` | People or groups the visitor says were affected, if specified |
| `supporting_evidence` | Concrete actions, words, outcomes, or examples described |
| `counterevidence` | Facts that complicate the initial interpretation, if supplied |
| `uncertainties` | Missing or disputed facts; never treated as adverse evidence |
| `change_indicator` | Observable evidence of correction or progress, if supplied |

The schema must preserve the difference between user-supplied facts and system-generated interpretations. A generated inference must cite the relevant prompt IDs and be labeled as an inference, not silently inserted as fact.

## Synthesis contract

Both LLM and deterministic paths consume the same evidence items and must produce these sections in order:

1. **The central incoherence to examine** — the most consequential supported tension between service obligation, conduct, and effects; if none is defensible, say so.
2. **Why it matters** — evidence-grounded consequence for people, responsibility, or work.
3. **What the evidence says** — connect specific observations across dimensions; distinguish sources and inference.
4. **What could change the interpretation** — counterevidence, context, alternative explanations, and material unknowns.
5. **What to do next** — a proportionate action, who can take it, and observable indicators of change.

The output should lead with the finding rather than disclaimers, name supported issues directly, avoid invented motives, and preserve visitor agency.

## Mode-specific integrity

- Self-reflection may ask the visitor to articulate their intention and commitment, but must still compare that account with conduct and consequences.
- Third-party reflection must not assert another person's private intent, motives, or willingness unless directly and appropriately evidenced by their own expressed words; even then, attribute the statement.
- Do not equate a single error with a pattern, or a good intention with a good outcome.
- Do not use the reflection as a standalone hiring, promotion, or removal decision.

## Validation cases required before implementation acceptance

1. **Strong supported tension:** stated commitment to collaboration, specific repeated conduct that blocks information or dissent, and described consequences for colleagues.
2. **Mixed evidence:** a difficult response to feedback followed by a concrete repair and changed behavior.
3. **Plausible contextual explanation:** unilateral action during a time-critical event with clear constraints and subsequent explanation.
4. **Insufficient evidence:** strong labels or reputation but no concrete example or reliable source.
5. **No defensible tension:** evidence broadly aligns with the role's obligations, while a non-material gap remains.
6. **Conflicting sources:** first-hand observation and second-hand report disagree.
7. **Unknown willingness or intention in third-party mode:** system does not infer private commitment from silence or outward behavior.
8. **Correction test:** the output specifies an observable next step without deciding suitability.

## Open design questions for validation

- Is eight prompts the right burden for the visitor, or should the sequence use progressive follow-up only when the prior answer identifies a material tension or gap?
- Should source type be selected explicitly for each example, or captured with a compact follow-up prompt?
- What is the best plain-language phrasing for commitment in third-party mode so it refers to role obligations rather than inferred inner motives?

Resolve these UX questions without weakening the locked stewardship model or its evidence requirements.
