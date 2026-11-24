import provider_exhaustion_candidate_policy as policy


def test_provider_exhaustion_policy_selects_only_the_public_commons_gold_star():
    lesson = {
        "id": policy.BENCHMARK_ID,
        "runtime_transfer": True,
    }
    selected = policy.select_provider_exhaustion_candidate(
        "When search services are unavailable, how should a guide answer a general question about civic commons without claiming official doctrine?",
        [lesson],
    )
    assert selected is not None
    assert selected["lesson"] is lesson
    assert selected["role"] == "core"


def test_provider_exhaustion_policy_rejects_missing_provider_outage_or_doctrine_boundary():
    lesson = {"id": policy.BENCHMARK_ID, "runtime_transfer": True}
    assert policy.select_provider_exhaustion_candidate(
        "How should a guide explain civic commons in general terms?",
        [lesson],
    ) is None
    assert policy.select_provider_exhaustion_candidate(
        "When search services are unavailable, how should a guide answer a general question about civic commons?",
        [lesson],
    ) is None


def test_provider_exhaustion_policy_requires_active_runtime_transfer_record():
    inactive = {"id": policy.BENCHMARK_ID, "runtime_transfer": False}
    assert policy.select_provider_exhaustion_candidate(
        "When search services are unavailable, how should a guide answer a general question about civic commons without claiming official doctrine?",
        [inactive],
    ) == []
