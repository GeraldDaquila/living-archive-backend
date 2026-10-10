"""Static regression QA for HRN-to-USE canonical doorway selection.

This verifies the closure route ranks against the earned perspective first and
keeps its fallback bounded to that perspective. Live relevance still requires
post-deployment E2E tests against canonical resources.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    require(SOURCE.startswith("# USE PRODUCTION VERSION: v489.82 — Focused HRN relational doorway selection"),
            "production version header drift")
    require('APP_VERSION = "v489.82"' in SOURCE, "APP_VERSION did not advance sequentially")
    require('if str(APP_VERSION) != "v489.82":' in SOURCE, "runtime version invariant drift")
    require('DEPLOYMENT_FINGERPRINT = "USE-v489.82-focused-hrn-relational-doorway"' in SOURCE,
            "deployment fingerprint drift")
    require('CANONICAL_BUILD_ID = "USE-BUILD-v489.82-focused-hrn-relational-doorway"' in SOURCE,
            "canonical build identity drift")

    start = SOURCE.find("async def _v48755_relational_return")
    end = SOURCE.find("# ---------------------------------------------------------------------", start)
    route = SOURCE[start:end]
    require(start >= 0 and end > start, "relational return route could not be isolated")
    focused = route.find('context_data = _original_fetch_canonical_context(doorway_query)')
    require(focused >= 0, "first retrieval does not use the focused earned-perspective query")
    require(route.find('profile = _base._inquiry_profile(doorway_query)') > focused,
            "profile is not calibrated against the same focused query")
    require('fallback_query = synthesis_query' not in route,
            "fallback reintroduces the entire transcript/ledger and query dilution")
    fallback = route.find("fallback_query = \" \".join(")
    require(fallback > focused, "bounded fallback is missing")
    fallback_block = route[fallback:route.find("fallback_data =", fallback)]
    for required in ("journey_synthesis", "completed_insight", "perspective_delta", "resource_fit", "next_horizon"):
        require(required in fallback_block, f"bounded fallback omits earned-perspective field: {required}")
    for forbidden in ("conversation", "thread_summary", "body_of_thought", "journey_ledger", "fractal_records", "round_synthesis_history", "original_question"):
        require(forbidden not in fallback_block, f"fallback reintroduces noisy field: {forbidden}")
    require("canonical_doorway" in route and '"canonical_doorway": None' in route,
            "no-fit outcome must remain available instead of forcing an unrelated gift")
    require("def _canonical_primary_from_docs" in SOURCE,
            "canonical evidence-ranked selection function is missing")
    print("V489.82 HRN RELATIONAL RETURN QA: PASS")
    print("focused_first_retrieval=True")
    print("bounded_earned_perspective_fallback=True")
    print("unrelated_doorway_forcing=absent")


if __name__ == "__main__":
    main()
