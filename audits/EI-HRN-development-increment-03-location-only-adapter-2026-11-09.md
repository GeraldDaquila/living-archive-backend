# EI–HRN Development Increment 03 — Location-only adapter

Date: 2026-11-09  
Branch: `dev/ei-security-and-hrn-adapter-20261109`  
Status: Development-only; not deployed.

## Change

Added a separate HRN REST operation:

- `POST /wp-json/living-archive/v1/emergency-resources`

The route accepts only:
- `country`
- `safety_stage`
- `safety_question`
- `safety_message` (the existing HRN safety prompt text, not a visitor answer)

It does not accept a visitor `message`, transcript, conversation history, or visitor-history payload. It does not call `rest_handler_inner()`, `safety_answer_class()`, or `safety_transition()`.

The route returns the supplied stage, question, and message unchanged, together with a resource list. The adapter attempts EI resolution for `general_emergency`, `medical`, and `crisis_support`. Only `SELECTED` EI results are rendered as EI resources. HRN's existing local resource bundle is retained as a continuity fallback and as a source of additional distinct alternatives. No numbers or URLs are synthesized.

The frontend now submits location to the dedicated route. It no longer sends the country as a visitor message to the ordinary conversation route. The frontend does not send conversation or visitor-history data during this operation. The script URL is cache-busted with an asset-version suffix.

## Protected invariants

Compared the following six method bodies against the frozen source baseline branch; all were identical:
- `deterministic_safety_signal()`
- `explicit_suicide_language()`
- `safety_answer_class()`
- `safety_transition()`
- `safety_response()`
- `rest_handler_inner()`

Static source checks confirmed:
- The dedicated resource route is registered.
- The adapter calls the EI public resolver when available.
- The adapter does not call the safety answer classifier.
- The frontend uses `LAHRN.emergency_endpoint`.
- The frontend location request contains no visitor `message`, conversation, or visitor-history fields.
- The adapter echoes the supplied safety question and stage.

## Known limitations / not yet verified

- PHP syntax validation passed for all PHP files in both plugins in GitHub Actions run [42583379198](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/42583379198).
- Frontend JavaScript syntax validation passed in the same run.
- Static location-only boundary assertions passed in the same run.
- No WordPress runtime/integration test has been executed.
- No browser E2E test has been run.
- No live request has yet confirmed that EI loads before the HRN callback in the target WordPress runtime, although the plugin loading hooks and public interface were inspected.
- EI's public route remains unauthenticated in the same way as the existing HRN public REST route; request throttling and abuse controls still need a separate review.
- HRN's legacy registry is still retained and is not independently reverified by this change.
- EI coverage remains incomplete for the ten-country HRN footprint.
- The adapter intentionally uses EI only when the selector returns `SELECTED`; equivalent or other non-selected states fall back to HRN resources.
- No deployment, WordPress write, registry migration, or production configuration change was performed.

## Next required gates

1. Run PHP syntax lint on both plugins and JS syntax validation.
2. Run a WordPress integration test with EI active and with EI unavailable.
3. Verify byte-for-byte preservation of safety stage, question, and message on a location-only request.
4. Verify the location-only request does not call the ordinary HRN conversation handler or advance the safety state.
5. Verify PH, US, DE, GB, and CN EI selection and fallback behavior; verify CA, AU, SG, HK, and NL use the legacy fallback until EI parity is established.
6. Run full HRN safety regression and browser E2E.
7. Review REST rate limiting and abuse protection.
8. Keep production frozen until all gates pass.
