"""Static regression QA for relevance-safe HRN-to-USE canonical doorway selection."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
BANK = (ROOT / "provider_bank.py").read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    require(SOURCE.startswith("# USE PRODUCTION VERSION: v489.86 — relational return topic-fit repair"),
            "production version header drift")
    require('APP_VERSION = "v489.86"' in SOURCE, "APP_VERSION did not advance sequentially")
    require('if str(APP_VERSION) != "v489.86":' in SOURCE, "runtime version invariant drift")
    require('DEPLOYMENT_FINGERPRINT = "USE-v489.86-relational-return-topic-fit"' in SOURCE,
            "deployment fingerprint drift")
    require('CANONICAL_BUILD_ID = "USE-BUILD-v489.86-relational-return-topic-fit"' in SOURCE,
            "canonical build identity drift")

    start = SOURCE.find("async def _v48755_relational_return")
    end = SOURCE.find("# ---------------------------------------------------------------------", start)
    route = SOURCE[start:end]
    require(start >= 0 and end > start, "relational return route could not be isolated")
    focused = route.find('context_data = _original_fetch_canonical_context(doorway_query)')
    require(focused >= 0, "first retrieval does not use the focused relational topic query")
    require('topic_anchor = original_question' in route, "original concern is not the first query anchor")
    require('Relational projection: distinguish what is observed from what is inferred in the relationship.' in route,
            "projection concern lacks a concise observation/inference retrieval anchor")
    require(route.find('profile = _base._inquiry_profile(doorway_query)') > focused,
            "profile is not calibrated against the same focused query")
    require('fallback_query = synthesis_query' not in route,
            "fallback reintroduces the entire transcript/ledger and query dilution")
    require('def _relational_return_direct_topic_fit(query, doc):' in SOURCE,
            "direct topic-fit boundary is missing")
    require('if primary and not _relational_return_direct_topic_fit(original_question, primary):' in route,
            "first selected doorway bypasses direct topic-fit validation")
    require('if primary and not _relational_return_direct_topic_fit(original_question, primary):' in route[route.find("fallback_query ="):],
            "fallback-selected doorway bypasses direct topic-fit validation")
    fallback = route.find("fallback_query = \" \".join(")
    require(fallback > focused, "bounded fallback is missing")
    fallback_block = route[fallback:route.find("fallback_data =", fallback)]
    for required in ("topic_anchor", "completed_insight", "perspective_delta", "journey_synthesis"):
        require(required in fallback_block, f"bounded fallback omits focused perspective field: {required}")
    for forbidden in ("conversation", "thread_summary", "body_of_thought", "journey_ledger", "fractal_records", "round_synthesis_history", "original_question", "resource_fit", "next_horizon"):
        require(forbidden not in fallback_block, f"fallback reintroduces noisy field: {forbidden}")
    require("canonical_doorway" in route and '"canonical_doorway": None' in route,
            "no-fit outcome must remain available instead of forcing an unrelated gift")
    require('re.split(r"(?<=[.!?])\\s+", completed)' in BANK,
            "Provider Bank sentence counter must split on whitespace correctly")
    require("response shape requires at least two complete sentences and 180 characters" in BANK,
            "Provider Bank does not enforce HRN's downstream response-shape floor")
    require("The response must contain at least two complete sentences and 180 characters." in BANK,
            "Provider Bank recovery prompt does not explain the response-shape failure")
    require("lanes.sort(key=_hrn_lane_priority)" in BANK, "HRN provider lanes are not ranked by observed health and quality")
    require("configured_priority.get(provider, len(configured_priority))" in BANK, "provider-order tie-breaker is missing")
    print("V489.86 HRN RELATIONAL RETURN QA: PASS")
    print("focused_topic_first_retrieval=True")
    print("direct_projection_or_observation_inference_fit=True")
    print("unrelated_doorway_forcing=absent")


if __name__ == "__main__":
    main()
