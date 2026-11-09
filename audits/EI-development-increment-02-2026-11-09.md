# EI Development Increment 02 — Resource-Only Bundle API
Date: 2026-11-09
Branch: `dev/ei-security-and-hrn-adapter-20261109`

## Added
A new public REST route has been added to the EI plugin source:
- `POST /wp-json/living-archive/emergency/v1/resolve-bundle`

Request contract:
- `service_needs`: array of one to ten service category keys.
- `location`: location evidence object (for a visitor-entered country, use `explicit_country`).
- `safety_state`: optional contextual state label; defaults to `unknown`.

Response contract:
- `operation: resource_location_resolution`
- `registry_version`
- `results`: one EI resolution result per requested service category.

The endpoint does not accept a visitor message, safety answer, or safety question. It does not call HRN, classify risk, or advance a safety state. It is a resource-resolution operation only.

## Why this is separate
HRN's current location-entry handler sends the country name through the ordinary conversation endpoint as the visitor's message. This new EI endpoint creates a clean target for the frontend's location-only operation. The frontend adapter has not yet been switched to it.

## Current integration limitation
The existing EI registry has five countries and ten resources. It does not yet contain the full HRN ten-country resource footprint, and some country/service combinations have no corresponding EI resource (including China crisis-support in the current EI dataset). Therefore, this endpoint must not yet replace HRN's resource output globally. The old HRN registry remains necessary until country/service parity is complete and verified.

## Static verification performed
- Route declaration present in the development-branch source.
- Handler requires a service list and location object.
- Handler returns a resource-only operation label.
- Handler contains no HRN safety classifier or transition call.
- HRN PHP blob remains unchanged from frozen baseline.
- EI remote HTTP fetch is absent from the updated update manager.
- No PHP runtime/lint or browser test is claimed.

## Next
1. Build a bounded HRN adapter that calls the new route only for location resolution and maps verified EI records to the HRN resource presentation shape.
2. Retain HRN registry fallback for any country/service with no eligible EI result.
3. Ensure location input never enters the visitor message, answer classifier, or state transition.
4. Complete resource parity and verification before activating EI for all visitor journeys.
