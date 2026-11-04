"""Regression tests for USE provider circuit resilience."""
import unittest
from provider_resilience import HEALTHY, OPEN, HALF_OPEN, new_state, blocked, acquire_probe, record_failure, record_success, aggregate_provider_health

class ProviderResilienceTests(unittest.TestCase):
    def test_transient_failure_opens_and_recovers(self):
        state=new_state("test","model")
        record_failure(state,"network_failure","timeout",now=100)
        self.assertEqual(state["state"],OPEN)
        self.assertTrue(blocked(state,now=110))
        self.assertFalse(blocked(state,now=131))
        self.assertEqual(state["state"],HALF_OPEN)
        self.assertTrue(acquire_probe(state))
        self.assertFalse(acquire_probe(state))
        record_success(state,now=132)
        self.assertEqual(state["state"],HEALTHY)

    def test_permanent_failure_quarantines_candidate(self):
        state=new_state("test","model")
        record_failure(state,"authentication","bad credentials",now=100)
        self.assertTrue(blocked(state,now=500))
        self.assertGreater(state["quarantine_until"],500)

    def test_failures_back_off_with_cap(self):
        state=new_state("test","model")
        delays=[record_failure(state,"provider_failure","x",now=100+i) for i in range(8)]
        self.assertEqual(delays[:4],[30.0,60.0,120.0,240.0])
        self.assertLessEqual(max(delays),300.0)

    def test_aggregate_health_reports_degradation(self):
        healthy=new_state("a","1")
        failed=new_state("b","1")
        record_failure(failed,"unavailable","down",now=100)
        self.assertEqual(aggregate_provider_health([healthy,failed]),"degraded")
        self.assertEqual(aggregate_provider_health([failed]),OPEN)

if __name__=="__main__":
    unittest.main()
