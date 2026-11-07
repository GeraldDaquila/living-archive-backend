import provider_bank as bank

def _reset():
    with bank._CAPACITY_METRICS_LOCK:
        bank._CAPACITY_METRICS.update({"attempts":0,"llm_successes":0,"exhaustions":0,"inflight":0})

def test_lifecycle_success_and_exhaustion_accounting():
    _reset()
    bank._capacity_begin_request(); bank._capacity_end_request(success=True)
    bank._capacity_begin_request(); bank._capacity_end_request(exhausted=True)
    with bank._CAPACITY_METRICS_LOCK:
        assert bank._CAPACITY_METRICS == {"attempts":2,"llm_successes":1,"exhaustions":1,"inflight":0}

def test_end_is_idempotently_bounded_against_underflow():
    _reset()
    bank._capacity_end_request()
    with bank._CAPACITY_METRICS_LOCK:
        assert bank._CAPACITY_METRICS["inflight"] == 0

def test_recovery_sequence_returns_to_zero_inflight():
    _reset()
    bank._capacity_begin_request(); bank._capacity_end_request(exhausted=True)
    bank._capacity_begin_request(); bank._capacity_end_request(success=True)
    with bank._CAPACITY_METRICS_LOCK:
        assert bank._CAPACITY_METRICS["attempts"] == 2
        assert bank._CAPACITY_METRICS["llm_successes"] == 1
        assert bank._CAPACITY_METRICS["exhaustions"] == 1
        assert bank._CAPACITY_METRICS["inflight"] == 0
