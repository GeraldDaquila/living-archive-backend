"""Static regression QA for relevance-safe HRN-to-USE canonical doorway selection."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]

SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
BANK = (ROOT / "provider_bank.py").read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    require(SOURCE.startswith("# USE PRODUCTION VERSION: v489.92 — HRN earned-perspective doorway return"),
            "production version header drift")
    require('APP_VERSION = "v489.92"' in SOURCE, "APP_VERSION did not advance sequentially")
    require('if str(APP_VERSION) != "v489.92":' in SOURCE, "runtime version invariant drift")
    require('DEPLOYMENT_FINGERPRINT = "USE-v489.92-hrn-earned-perspective-doorway-fit"' in SOURCE,
            "deployment fingerprint drift")
    require('CANONICAL_BUILD_ID = "USE-BUILD-v489.92-hrn-earned-perspective-doorway-fit"' in SOURCE,
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
    require('def _relational_return_direct_topic_fit(query, doc):' in SOURCE,
            "direct topic-fit boundary is missing")
    require('query_terms = set(_subject_terms(q))' in SOURCE,
            "general relational topic evidence terms are missing")
    require('material_tokens = set(re.findall(r"[a-z0-9]+", body_text))' in SOURCE,
            "body corroboration is not separated from title overlap")
    require('sentence_specific_hits >= 2' in SOURCE,
            "general relational return must cluster substantive query terms within a sentence")
    require('(specific_title_hits and len(body_hits) >= 2)' in SOURCE,
            "distinctive title evidence must be corroborated by body evidence")
    require('len(specific_terms) == 1' in SOURCE and 'specific_title_hits and specific_body_hits' in SOURCE,
            "single-topic queries require title and body agreement")
    require('or _relational_return_earned_focus_fit(direct_topic_query, doc)' in route,
            "first candidate set is ranked before topic-fit filtering")
    require('or _relational_return_earned_focus_fit(fallback_query, doc)' in route,
            "fallback candidate set is ranked before topic-fit filtering")
    require('fallback_query = synthesis_query' not in route,
            "fallback reintroduces the entire transcript/ledger and query dilution")
    fallback = route.find("fallback_query = \" \".join(")
    require(fallback > focused, "bounded fallback is missing")
    fallback_block = route[fallback:route.find("fallback_data =", fallback)]
    for required in ("underlying_need", "completed_insight", "perspective_delta", "current_terrain", "unresolved"):
        require(required in fallback_block, f"bounded fallback omits focused perspective field: {required}")
    for forbidden in ("conversation", "thread_summary", "body_of_thought", "fractal_records", "round_synthesis_history", "original_question", "topic_anchor", "journey_synthesis", "resource_fit", "next_horizon"):
        require(forbidden not in fallback_block, f"fallback reintroduces noisy field: {forbidden}")
    require("def _relational_return_topic_anchor(original_question, underlying_need, perspective_delta):" in SOURCE,
            "earned relational topic anchor is missing")
    require("def _relational_return_earned_focus_fit(query, doc):" in SOURCE,
            "earned-focus evidence gate is missing")
    require('profile["primary"] = "relational"' in route and 'profile["relational"] = True' in route,
            "HRN return route does not preserve its relational specialist boundary")
    require("direct_topic_query = " in route and "underlying_need, perspective_delta, completed_insight" in route,
            "canonical ranking does not use the earned perspective")
    require("json.dumps(journey_ledger" not in fallback_block, "fallback serializes the entire journey ledger")
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
    print("V489.92 HRN RELATIONAL RETURN QA: PASS")
    print("direct-fit-filter_before_ranking=True")
    print("unrelated_doorway_forcing=absent")


if __name__ == "__main__":
    main()
    runpy.run_path(str(ROOT / "QA/V489_92_HRN_EARNED_FOCUS_QA.py"), run_name="__main__")
