# EI–HRN Development Increment 07: Mini-USE Workspace and Test Boundary

Date: 2026-11-09  
Branch: `dev/ei-security-and-hrn-adapter-20261109`  
Scope: read-only Render workspace/service inspection and expanded isolated adapter regression tests. No Render service configuration changes, no deployments, no WordPress writes.

## 1. Workspace direction

The user designated **Mini-USE-Payhip** as the preferred Render workspace for this investigation, in preference to Standalone QA because Standalone QA already hosts five other projects.

Render workspace:
- Name: Mini-USE Workspace
- Workspace ID: `tea-damhgg2d0e5s73ffis1g`

This designation is a workspace preference, not permission to repurpose or overwrite existing Catalogue services.

## 2. Mini-USE services inspected

Three services were returned in the Mini-USE workspace:

### Catalogue production service
- Name: `mini-use-payhip`
- Service ID: `srv-dami28f40ujc73b15ej0`
- Repository: `GeraldDaquila/mini-use-payhip`
- Branch: `main`
- Runtime: Python / FastAPI
- Plan: Free
- Auto-deploy: disabled
- Region: Oregon
- Decision: protect; do not alter.

### Stewardship service
- Name: `mini-use-payhip-stewardship`
- Service ID: `srv-dann00n40ujc73cg0t60`
- Repository: `GeraldDaquila/mini-use-payhip`
- Branch: `stewardship-m0.9.68-audit`
- Runtime: Python / FastAPI
- Plan: Free
- Auto-deploy: enabled
- Region: Oregon
- Decision: protect; do not alter.

### Candidate service
- Name: `mini-use-payhip-m01554-candidate`
- Service ID: `srv-db5jcg59fdbs73d3enfg`
- Repository: `GeraldDaquila/mini-use-payhip`
- Branch: `fix/case-discovery-evidence-gate`
- Runtime: Python / FastAPI
- Plan: Free
- Auto-deploy: disabled
- Region: Singapore
- Last listed live deploy: `dep-dbjvbjqjnfac73957mqg`
- Deploy commit: `8fbb5c3edb5c9b6ec0ab3b0df7de3202c7181640`
- Commit message: "Add privacy regression to active candidate branch"
- Candidate source identifies Mini-USE Payhip Catalogue Navigator, version M0.15.81, and loads the 565-entry Catalogue at startup.
- Requirements include FastAPI, Uvicorn and Pydantic; no PHP or WordPress runtime.
- Recent available logs show the service shut down on November 3 and started again later that morning; no evidence from these logs establishes HRN test capability.

## 3. Technical conclusion

The Mini-USE workspace is the user's preferred Render workspace, but its existing candidate service is not a suitable execution target for the EI–HRN PHP plugin. It is a running Catalogue application tied to the Mini-USE repository and its own candidate branch.

Repurposing that service, changing its repository/branch, replacing its start command, or adding HRN code to the Catalogue would risk unrelated functionality. None of those actions was taken.

A full WordPress integration test requires a WordPress/PHP runtime and a controlled WordPress database/plugin bootstrap. The existing Mini-USE Python service cannot provide that merely by being in the preferred workspace.

Current safe approach:
- Continue source-level and isolated PHP execution tests in GitHub Actions.
- Keep Mini-USE workspace as the preferred location for any future separately isolated test resource, if one is later justified and authorized.
- Do not create a new Render service or incur costs without explicit approval.
- Do not modify the Catalogue production, stewardship, or candidate services.
- Continue to seek a genuine WordPress staging target for full plugin loading, REST, and browser E2E validation.

## 4. Additional regression coverage

Commit:
- `ce2611ba5b7037998be72976801340bd3670f7cd`
- https://github.com/GeraldDaquila/living-archive-backend/commit/ce2611ba5b7037998be72976801340bd3670f7cd

Added isolated HRN handler checks for:
- EI malformed selection output is ignored and HRN continuity resources remain available.
- Malformed EI output cannot alter active HRN safety stage or question.
- Malformed EI output is correctly labelled as HRN legacy fallback.
- EI receives only resource need, explicit location, safety-state context, and policy; not the HRN prompt or visitor answer.
- Adapter route is POST-only.
- Adapter route accepts only country, safety stage, existing safety question, and existing HRN prompt.
- Visitor message, conversation, visitor history, and full transcript fields are absent from the EI adapter route contract.
- Country, safety-question, and HRN-prompt length limits are enforced by route validators.

CI:
- Run ID: `42588970645`
- Result: success
- https://github.com/GeraldDaquila/living-archive-backend/actions/runs/42588970645
- All workflow steps passed, including PHP syntax, JS syntax, boundary assertions, isolated PHP handler execution, and pytest source-contract tests.

## 5. Release status

Development only. No PR, merge, main-branch update, Render deployment, WordPress write, or production test was performed.

The successful CI run validates the expanded isolated test harness and source contract only. It does not establish full WordPress integration, live EI registry correctness, browser E2E, or production endpoint security.
