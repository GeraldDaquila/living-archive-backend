"""Offline simulation for Predictive Provider Assignment v1.

This test does not call providers or alter production routing. It models the
observed timeout pattern: candidates that repeatedly approach the request
deadline should lose first-choice priority to currently reliable candidates.
"""
from dataclasses import dataclass
from math import exp


@dataclass
class Evidence:
    name: str
    health: str = "healthy"
    quality_failures: int = 0
    consecutive_failures: int = 0
    transport_failures: int = 0
    low_latency: bool = True
    ewma_latency: float = 0.0
    attempts: int = 0
    timeouts: int = 0
    last_success: float = 0.0


def readiness(item: Evidence, budget: float = 4.0):
    # Hard gates remain outside this ranking layer.
    health_rank = 0 if item.health == "healthy" else 1
    latency = item.ewma_latency or budget * 0.5
    deadline_fit = min(2.0, latency / max(budget, 0.1))
    timeout_risk = item.timeouts / max(1, item.attempts)
    return (
        health_rank,
        item.quality_failures,
        item.consecutive_failures,
        round(timeout_risk, 4),
        round(deadline_fit, 4),
        0 if item.low_latency else 1,
        item.transport_failures,
        -item.last_success,
    )


def rank(items):
    return sorted(items, key=readiness)


def scenario_repeated_deadline_timeouts():
    items = [
        Evidence("workers_ai", ewma_latency=4.05, attempts=5, timeouts=4, last_success=10),
        Evidence("gemini", ewma_latency=3.95, attempts=4, timeouts=3, last_success=20),
        Evidence("groq", ewma_latency=1.10, attempts=8, timeouts=0, last_success=30),
    ]
    ordered = [x.name for x in rank(items)]
    assert ordered[0] == "groq", ordered
    return ordered


def scenario_fast_explicit_rate_limit():
    # A fast rejection should remain a health/admission concern; predictive
    # latency must not incorrectly treat a 0.3-second 429 as good readiness.
    items = [
        Evidence("mistral", health="open", ewma_latency=0.35, attempts=4, timeouts=0),
        Evidence("groq", ewma_latency=1.2, attempts=5, timeouts=0),
    ]
    ordered = [x.name for x in rank(items)]
    assert ordered[0] == "groq", ordered
    return ordered


def scenario_recovery_not_permanently_blacklisted():
    # Recent good latency with reduced timeout risk should allow recovery.
    recovered = Evidence("workers_ai", ewma_latency=1.4, attempts=6, timeouts=1, last_success=50)
    slow = Evidence("gemini", ewma_latency=3.9, attempts=6, timeouts=4, last_success=40)
    ordered = [x.name for x in rank([slow, recovered])]
    assert ordered[0] == "workers_ai", ordered
    return ordered


if __name__ == "__main__":
    print("deadline_timeouts:", scenario_repeated_deadline_timeouts())
    print("fast_rate_limit:", scenario_fast_explicit_rate_limit())
    print("recovery:", scenario_recovery_not_permanently_blacklisted())
    print("PASS")
