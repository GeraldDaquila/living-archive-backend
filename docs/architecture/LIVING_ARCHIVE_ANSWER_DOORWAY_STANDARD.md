# Living Archive Answer + Doorway Standard
Version: 1.0.0
Status: canonical presentation contract
Applies to: The Guide / USE, HRN, FSD, SPE, Public Living Archive Navigator, Mini-USE, and future visitor-facing modules.

## Purpose
Every visitor-facing module should present a complete answer or result first, then offer a distinct, optional doorway into a verified Living Archive resource when that resource materially advances the visitor's inquiry. The doorway is orientation, not promotion.

### The Guide's doorway-by-default invariant
For every eligible substantive Guide response, evaluate a separate, bounded selection for one verified Living Archive continuation by default. This applies regardless of retrieval context, answer provenance, provider route, deterministic recovery, or Gold Star pathway. A doorway is optional navigation and must never weaken, shorten, distort, or become a prerequisite for the answer.

Omit the doorway only when the visitor explicitly declines further navigation, no materially relevant verified canonical destination passes the applicable relevance and authority checks, a reviewed Gold Star exception authorizes omission, or safety/protected-access handling requires a different handoff. A general-knowledge answer is not itself a reason to omit a doorway. Conversely, a broad registry fallback must not attach an adjacent but unrelated resource after the bounded canonical selector finds no relevant destination. At most one doorway is rendered for a Guide answer.

A failed resolver or source-verification pass is recorded as a selection failure, not misreported as an intentional no-destination result. Never invent a destination. The complete answer remains useful without the doorway.

## Shared visual form
1. A restrained pale cream panel, thin neutral border, and muted gold left accent.
2. The small uppercase label **CONTINUE EXPLORING**.
3. A concise, source-grounded rationale explaining the specific contribution of the destination.
4. A clear, underlined destination title.
5. Responsive layout, readable contrast, and no decorative animation.

## Shared data contract
A doorway item is:
- `title`: non-empty visitor-facing canonical title, maximum 180 characters.
- `url`: canonical absolute HTTPS URL on `geralddaquila.com`, with no credentials, query, or fragment.
- `rationale`: non-empty explanation of the destination's specific contribution, maximum 600 characters.
- `kind`: optional internal adapter hint; it never changes the visitor-facing label or bypasses validation.

Incomplete, unverified, unrelated, or unsafe items are omitted. Never invent a destination or rationale to fill the panel. No doorway is a valid result.


## Canonical resource doorway and conversational continuation are separate affordances

The canonical resource doorway and a conversational reply panel serve different visitor actions. They are independent and may coexist; neither substitutes for the other.

### Canonical resource doorway decision

For every eligible substantive Guide answer, evaluate the bounded canonical selector independently of answer formation. The backend must preserve an explicit, auditable decision state:

- `selected`: one verified, materially relevant canonical destination is available. Render it using the shared **CONTINUE EXPLORING** resource presentation.
- `omit` with `NO_RELEVANT_DESTINATION_AFTER_BOUNDED_SEARCH`: the bounded selector completed and no candidate passed relevance and authority checks. This is an intentional, evaluated omission.
- `omit` with `AUTHORIZED_OMISSION`: a specific policy authority applies, such as explicit visitor refusal, a reviewed Gold Star exception, or a safety/protected-access override. Preserve the authority/source in the decision metadata.
- `omit` with `RETRIEVAL_OR_VERIFICATION_FAILURE`: selection could not be completed or verified. This is a failure state, not proof that no relevant destination exists; it must not be certified or described as an intentional omission.

The response contract should retain the decision, status, whether selection was evaluated, source, and a concise omission/failure reason where applicable. A selected doorway must carry its validated title, canonical URL, and grounded rationale. Never infer a URL or rationale from the answer text or from the presence of a conversational question.

### Conversational continuation affordance

The reply panel is a separate interaction affordance. Render it only when the final answer genuinely invites a reply and the visitor has not declined conversational follow-up. It is not a canonical Archive resource, does not count toward the one-resource-doorway limit, and must not be presented or logged as a successful canonical selection.

### Coexistence and precedence

- A selected canonical resource doorway and a genuine conversational invitation may appear together: the standard resource card remains in its dedicated recommendation container, while the reply panel remains in the response conversation surface.
- If no materially relevant verified destination exists, omit the resource card. A genuine conversational invitation may still render its reply panel.
- If canonical selection or verification fails, omit the resource card and retain an explicit failure state. Do not silently downgrade the failure to `NO_RELEVANT_DESTINATION_AFTER_BOUNDED_SEARCH`. A reply panel may still render if independently warranted and safe.
- Explicit refusal of a resource doorway suppresses the resource card. Explicit refusal of conversational follow-up suppresses the reply panel. These are distinct visitor choices; one must not be inferred from the other.
- Safety and protected-access handoffs retain precedence over ordinary resource cards and conversational continuation.
- At most one canonical resource doorway is rendered per Guide answer. The reply panel is not a doorway and does not violate this invariant.

The standard visitor presentation remains the default for a verified canonical destination. The conversational presentation is complementary, not an alternative resource-doorway template. Presentation follows the visitor's next useful action while the canonical resource contract remains stable.

## Module adapters preserve meaning
- **The Guide / USE:** adapt its authoritative `recommendation` / `doorway` object. Preserve registry-authored rationale and canonical selection authority.
- **HRN:** adapt a selected canonical resource plus its grounded resource introduction. Do not turn conversational prompts, junction controls, or safety resources into ordinary Archive doorways.
- **FSD:** adapt only `archive_references` explicitly marked `conceptual_context_only`, each with a title-grounded rationale. State that these references explain concepts and do not corroborate the respondent-reported episode. Do not imply a diagnosis, score, or stable system capacity.
- **SPE:** preserve the three selected canonical destinations and their individually grounded `why_each` explanations. The shared renderer changes presentation only; it does not change selection, ordering, access boundaries, or the three-door contract.
- **Public Living Archive Navigator:** preserve its clarification flow and three selected public destinations. The shared renderer does not change public T1–T3 corpus boundaries or Navigator selection.
- **Mini-USE:** preserve catalogue synthesis, selected doors, and access classification. The shared renderer does not alter Mini-USE retrieval, ranking, or its Stewardship Catalogue boundary.

## Trust and rendering requirements
- Validate URLs at the final browser boundary: HTTPS only, exact host `geralddaquila.com`, no username/password, non-default port, query, or fragment.
- Use DOM creation and `textContent`; never interpolate titles, rationales, or URLs into HTML strings.
- The Guide's Markdown response is parsed in a detached template, stripped of executable/active elements and all attributes, and only then inserted. Markdown links survive only when they pass the same first-party canonical URL validator.
- A shared WordPress `rest_post_dispatch` boundary applies the same canonical URL and non-generic rationale checks to SPE and Public Navigator responses before they leave WordPress. Invalid selections are removed and `why_each` is reconciled with the remaining destinations; the module's reflection and reasoning are left untouched.
- Enforce field length limits and omit malformed entries.
- Keep the answer/result complete independently of the doorway.
- Do not fabricate a fallback doorway. Clear stale doorway content when a new request starts or when no valid item is returned.
- Keep safety/emergency handoffs and protected-access rules outside the ordinary doorway renderer.

## Synchronization
Backend and module adapters may retain their native response envelopes. Each adapter must map only trusted fields into the shared item contract above. The renderer is versioned independently and must not own retrieval, relevance, canonical authority, or module reasoning.

## Deliberate non-applications
The shared component is for an answer/result followed by one or more canonical destinations. It is not a universal replacement for every link or result card on the site. Atlas Finder's image/map results remain visual search results. Glossary Intelligence's term definitions, related-term navigation, and lineage listings retain their native information architecture. These interfaces should use the shared doorway only if a distinct, reasoned canonical continuation is introduced; do not relabel every result link as a doorway.
