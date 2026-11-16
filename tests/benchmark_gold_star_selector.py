"""Reproducible, non-gating microbenchmark for Gold Star selector indexing.

Reports p50/p95 selection latency for the legacy algorithm and indexed runtime.
No timing threshold is asserted because shared CI runners are noisy.
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

# Direct script execution sets sys.path[0] to tests/, not the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gold_star_lessons as lessons


def legacy_select(query: str, candidates):
    normalized = lessons._normalized_phrase(query)
    exact = [
        item for item in candidates
        if lessons._normalized_phrase(item["query"]) == normalized
    ]
    if len(exact) == 1:
        return exact[0]["id"]
    query_terms = lessons._tokens(query)
    if len(query_terms) < 2:
        return None
    normalized_query_terms = lessons._concept_terms(query)
    ranked = []
    for item in candidates:
        if not item["runtime_transfer"]:
            continue
        signature = lessons._lesson_signature(item)
        shared_signature = normalized_query_terms & signature
        shared_variant = (
            lessons._concept_terms(" ".join(item["variants"]))
            & normalized_query_terms
        )
        reasoning = lessons._concept_terms(item.get("reasoning_family", ""))
        shared_family = normalized_query_terms & reasoning
        if len(shared_signature) < 2:
            continue
        coverage = len(shared_signature) / max(1, len(normalized_query_terms))
        if coverage < 0.20:
            continue
        score = min(
            0.94,
            0.42 + 0.08 * len(shared_signature)
            + 0.08 * len(shared_family) + 0.04 * len(shared_variant)
            + 0.12 * coverage,
        )
        ranked.append((score, len(shared_signature), item["id"]))
    if not ranked:
        return None
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    return ranked[0][2]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def measure(fn, queries, rounds=250):
    samples = []
    for _ in range(rounds):
        started = time.perf_counter_ns()
        for query in queries:
            fn(query)
        samples.append((time.perf_counter_ns() - started) / len(queries) / 1_000)
    return statistics.median(samples), percentile(samples, 0.95)


def main():
    base = list(lessons._LESSONS)
    queries = sorted({
        item["query"] for item in base
    } | {
        variant for item in base for variant in item["variants"]
    } | {
        "What is the weather tomorrow?",
        "Convert 25 dollars to pesos.",
        "How do I reset a forgotten password?",
    })
    if len(queries) > 80:
        stride = max(1, len(queries) // 80)
        queries = queries[::stride][:80]

    print(f"approved_registry_lessons={len(base)} benchmark_queries={len(queries)}")
    for size in (len(base), 150, 300, 500, 1000):
        candidates = list(base)
        while len(candidates) < size:
            i = len(candidates)
            item = {
                "id": f"synthetic-{i}",
                "query": f"Synthetic unrelated topic {i}",
                "known_theme": f"synthetic filler category {i}",
                "assertions": [],
                "runtime_transfer": True,
                "reasoning_family": f"synthetic_family_{i}",
                "variants": [],
            }
            item["signature_terms"] = lessons._lesson_signature(item)
            item["variant_terms"] = set()
            item["reasoning_terms"] = lessons._concept_terms(item["reasoning_family"])
            candidates.append(item)

        def indexed(query):
            old = lessons._LESSONS
            try:
                lessons._LESSONS = candidates
                result = lessons.select_lesson(query)
                return result["benchmark_id"] if result else None
            finally:
                lessons._LESSONS = old

        def legacy(query):
            return legacy_select(query, candidates)

        # Warm both code paths before collecting samples.
        for query in queries[:10]:
            indexed(query)
            legacy(query)
        old_p50, old_p95 = measure(legacy, queries)
        new_p50, new_p95 = measure(indexed, queries)
        print(
            f"lessons={size} legacy_us_p50={old_p50:.2f} legacy_us_p95={old_p95:.2f} "
            f"indexed_us_p50={new_p50:.2f} indexed_us_p95={new_p95:.2f} "
            f"p50_speedup={old_p50 / max(new_p50, 0.001):.2f}x"
        )


if __name__ == "__main__":
    main()
