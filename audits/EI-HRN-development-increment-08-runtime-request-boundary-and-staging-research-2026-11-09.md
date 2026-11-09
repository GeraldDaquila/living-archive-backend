# EI–HRN Development Increment 08: Runtime Request Boundary and Staging Research

Date: 2026-11-09  
Branch: `dev/ei-security-and-hrn-adapter-20261109`  
Scope: harden resource-only request contract; read-only WordPress production inspection; research official WordPress.com staging eligibility. No production writes or staging creation.

## 1. Production environment confirmation

Cowboy MCP read-only checks returned:
- Site: Life.Understood. (`https://geralddaquila.com`)
- Environment: `production`
- WordPress: 7.1.4
- PHP: 8.4.27
- MariaDB: 11.8.9
- Site Health: 9 good, 0 recommended, 0 critical.
- Live HRN plugin active: 0.5.333.
- Live EI plugin active: 0.1.2.

This confirms the connected WordPress site is production. No test POST, file write, plugin activation change, or settings change was performed.

## 2. Important REST boundary discovery and correction

A WordPress REST route's registered argument schema is not by itself a sufficient guarantee that extra request parameters will be rejected by the callback. The resource-only handler previously read only its expected fields, but it did not explicitly reject extra visitor-answer or transcript fields.

Updated `plugins/human-relational-navigator/human-relational-navigator.php`:
- Reads the request parameter map.
- Explicitly rejects visitor/conversation fields: `message`, `original_question`, `guide_question`, `query`, `conversation`, `visitor_history`, `full_conversation`, `unit_turns`, and `session_id`.
- Returns `lah_rn_visitor_content_not_accepted` with HTTP 400.
- Does not log or forward rejected content.

Expanded `tests/php/test_hrn_resource_location_handler.php`:
- Simulates an extra visitor answer field and asserts rejection.
- Simulates a conversation transcript field and asserts rejection.
- Retains prior tests for the route's allowlisted argument registration and input bounds.

Commits:
- Handler: `a9646716c1776d502516dfd05a317042c98017b1`
- Regression tests: `39d58afbeb0d4d5715a8d5d4f6b77dddf562ff3b`

CI:
- Run ID: `42589494475`
- Result: success
- https://github.com/GeraldDaquila/living-archive-backend/actions/runs/42589494475
- PHP syntax, JavaScript syntax, boundary assertions, isolated PHP execution tests, and source-contract tests passed.

This remains isolated PHP execution under minimal WordPress stubs, not yet an actual WordPress REST bootstrap or browser test.

## 3. WordPress.com staging research

Official WordPress.com support documentation (reviewed October 30, 2026) says:
- Native staging is available on WordPress.com Business and Commerce plans.
- Legacy Pro does not include staging; the site must switch to Business or Commerce.
- A staging environment is created from the Hosting Dashboard using the Production dropdown and “Add staging site”.
- A staging site is decoupled from production and marked with `WP_ENVIRONMENT_TYPE=staging`.
- One staging site can be created per production site.
- Production and staging share storage, split 50/50.
- The clone copies plugins, themes, media, users, configuration options, API keys and site database data.
- Database/file sync exists in both directions, so staging-to-production sync must remain out of scope for this safety-critical test effort.

Official source:
https://wordpress.com/support/how-to-create-a-staging-site/

The connected Cowboy MCP read-only interface does not expose the account's WordPress.com plan tier or a staging-site provisioning action. The site's plan eligibility therefore remains unknown. No staging environment was created.

The copied configuration/API keys and database contents require an explicit security review before using a full clone. We should not sync any staging content or database back to production as part of this integration.

## 4. Alternative test execution

The lowest-risk next technical path is an isolated WordPress runtime in GitHub Actions:
- Start a disposable WordPress + MariaDB test instance in the workflow.
- Install the exact development-branch EI and HRN plugin sources.
- Supply only the minimal test fixture needed for the canonical retriever dependency absent from this repository source snapshot.
- Boot WordPress and dispatch real REST requests to the adapter.
- Verify route registration, validation, error serialization, EI integration, and HRN state preservation.
- Keep all test data ephemeral; no production credentials or live emergency resource requests.

A separate WordPress.com staging clone may be useful for browser-level validation only if plan eligibility is confirmed and clone security implications are accepted. WordPress Studio is also a documented local development option; it is not required to complete the CI REST integration test.

## 5. Release status

Development branch only. No PR, merge, main update, Render deployment, WordPress production write, or staging creation.

The runtime rejection is now tested by the isolated handler harness and source-contract CI. It has not been deployed to the live site. The next gate is real WordPress bootstrap/REST integration in ephemeral CI, followed by browser E2E in a safe staging environment.
