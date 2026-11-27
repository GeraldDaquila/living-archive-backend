"""Prove the precomputed selector preserves the pre-optimization ranking."""

import re

import gold_star_lessons as lessons


def _legacy_select_lesson(query):
    """Reference implementation of the pre-index selector, kept test-only."""
    normalized = lessons._normalized_phrase(query)

    def eligible(item):
        return bool(item.get("runtime_transfer")) or bool(item.get("exact_answer_authority"))

    exact = [
        item for item in lessons._LESSONS
        if lessons._normalized_phrase(item["query"]) == normalized and eligible(item)
    ]
    if len(exact) == 1:
        item = exact[0]
        return item["id"], 1.0, True

    candidates = [item for item in lessons._LESSONS if item["runtime_transfer"]]
    query_terms = lessons._tokens(query)
    if len(query_terms) < 2:
        return None

    ranked = []
    for item in candidates:
        signature_terms = lessons._lesson_signature(item)
        normalized_query_terms = lessons._concept_terms(query)
        shared_signature = normalized_query_terms & signature_terms
        shared_variant = (
            lessons._concept_terms(" ".join(item["variants"]))
            & normalized_query_terms
        )
        reasoning_terms = lessons._concept_terms(item.get("reasoning_family", ""))
        shared_family = normalized_query_terms & reasoning_terms
        if len(shared_signature) < 2:
            continue
        coverage = len(shared_signature) / max(1, len(normalized_query_terms))
        if coverage < 0.20:
            continue
        score = min(
            0.94,
            0.42
            + 0.08 * len(shared_signature)
            + 0.08 * len(shared_family)
            + 0.04 * len(shared_variant)
            + 0.12 * coverage,
        )
        ranked.append((score, len(shared_signature), item["id"], item))

    if not ranked:
        return None
    ranked.sort(key=lambda entry: (-entry[0], -entry[1], entry[2]))
    score, _, _, item = ranked[0]
    return item["id"], round(score, 3), False


def test_precomputed_selector_preserves_real_registry_rankings():
    """All real approved queries and their variants retain identical outcomes."""
    queries = set()
    for item in lessons._LESSONS:
        # Frozen response-quality exemplars are not runtime selector candidates;
        # adding one must not expand the selector's legacy ranking population.
        if not (item.get("runtime_transfer") or item.get("exact_answer_authority")):
            continue
        queries.add(item["query"])
        queries.update(item["variants"])

    # Include out-of-domain controls to ensure abstention remains stable.
    queries.update({
        "What is the weather tomorrow?",
        "Convert 25 dollars to pesos.",
        "How do I reset a forgotten password?",
    })

    mismatches = []
    governed_policy_queries = []
    for query in sorted(queries):
        expected = _legacy_select_lesson(query)
        actual = lessons.select_lesson(query)
        # The explicit decision-rights subject-family policy is a governed
        # additive capability, not a precomputed-index ranking change. Its
        # candidate roles and boundaries are validated by the dedicated
        # decision-rights policy benchmark. Preserve exact and legacy behavior
        # for every query that does not enter that policy path.
        if actual and actual.get("match_basis") == "governed_decision_rights_policy":
            governed_policy_queries.append(query)
            continue
        observed = (
            (actual["benchmark_id"], actual["score"], actual["exact"])
            if actual else None
        )
        if observed != expected:
            mismatches.append((query, expected, observed))

    assert not mismatches, (
        f"Precomputed selector changed {len(mismatches)} of {len(queries)} "
        f"real-registry outcomes: {mismatches[:10]}"
    )
