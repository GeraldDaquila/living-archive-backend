# Living Archive Answer + Doorway Standard
Version: 1.0.0
Status: canonical presentation contract
Applies to: The Guide / USE, HRN, FSD, SPE, Public Living Archive Navigator, Mini-USE, and future visitor-facing modules.

## Purpose
Every visitor-facing module should present a complete answer or result first, then offer a distinct, optional doorway into a verified Living Archive resource when that resource materially advances the visitor's inquiry. The doorway is orientation, not promotion.

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

## Module adapters preserve meaning
- **The Guide / USE:** adapt its authoritative `recommendation` / `doorway` object. Preserve registry-authored rationale and canonical selection authority.
- **HRN:** adapt a selected canonical resource plus its grounded resource introduction. Do not turn conversational prompts, junction controls, or safety resources into ordinary Archive doorways.
- **FSD:** adapt only `archive_references` explicitly marked `conceptual_context_only`. State that these references explain concepts and do not corroborate the respondent-reported episode. Do not imply a diagnosis, score, or stable system capacity.
- **SPE:** preserve the three selected canonical destinations and their individually grounded `why_each` explanations. The shared renderer changes presentation only; it does not change selection, ordering, access boundaries, or the three-door contract.
- **Public Living Archive Navigator:** preserve its clarification flow and three selected public destinations. The shared renderer does not change public T1–T3 corpus boundaries or Navigator selection.
- **Mini-USE:** preserve catalogue synthesis, selected doors, and access classification. The shared renderer does not alter Mini-USE retrieval, ranking, or its Stewardship Catalogue boundary.

## Trust and rendering requirements
- Validate URLs at the final browser boundary: HTTPS only, exact host `geralddaquila.com`, no username/password, non-default port, query, or fragment.
- Use DOM creation and `textContent`; never interpolate titles, rationales, or URLs into HTML strings.
- Enforce field length limits and omit malformed entries.
- Keep the answer/result complete independently of the doorway.
- Do not fabricate a fallback doorway. Clear stale doorway content when a new request starts or when no valid item is returned.
- Keep safety/emergency handoffs and protected-access rules outside the ordinary doorway renderer.

## Synchronization
Backend and module adapters may retain their native response envelopes. Each adapter must map only trusted fields into the shared item contract above. The renderer is versioned independently and must not own retrieval, relevance, canonical authority, or module reasoning.
