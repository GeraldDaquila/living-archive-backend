import threading
import unittest
from unittest.mock import patch

import provider_quota_control as quota


class ProviderQuotaAdmissionTests(unittest.TestCase):
    def setUp(self):
        quota._reset_for_tests()

    def test_reservation_releases_concurrency_on_exit(self):
        with patch.dict("os.environ", {"USE_QUOTA_MAX_INFLIGHT_PROVIDER": "1", "USE_QUOTA_MAX_INFLIGHT_MODEL": "1"}, clear=False):
            first = quota.reserve("groq", "model-a", [{"role": "user", "content": "hello"}], 100)
            with self.assertRaises(quota.QuotaAdmissionDenied) as caught:
                quota.reserve("groq", "model-a", [{"role": "user", "content": "second"}], 100)
            self.assertEqual(caught.exception.reason, "provider_concurrency_cap")
            first.release()
            with quota.reserve("groq", "model-a", [{"role": "user", "content": "third"}], 100):
                self.assertEqual(quota.snapshot()["active_provider_calls"]["groq"], 1)
        self.assertEqual(quota.snapshot()["active_provider_calls"]["groq"], 0)

    def test_rpm_budget_rejects_without_admitting(self):
        with patch.dict("os.environ", {"USE_QUOTA_TEST_RPM": "1"}, clear=False):
            with quota.reserve("test", "model-a", "first request", 10):
                pass
            with self.assertRaises(quota.QuotaAdmissionDenied) as caught:
                quota.reserve("test", "model-b", "second request", 10)
            self.assertEqual(caught.exception.reason, "rpm_budget_exhausted")
            self.assertEqual(quota.snapshot()["active_provider_calls"].get("test", 0), 0)

    def test_tpm_budget_rejects_request_larger_than_window(self):
        with patch.dict("os.environ", {"USE_QUOTA_TEST_TPM": "50"}, clear=False):
            with self.assertRaises(quota.QuotaAdmissionDenied) as caught:
                quota.reserve("test", "model-a", "x" * 1000, 100)
            self.assertEqual(caught.exception.reason, "tpm_budget_exhausted")

    def test_concurrent_admission_never_exceeds_provider_cap(self):
        cap = 2
        barrier = threading.Barrier(8)
        admitted = []
        lock = threading.Lock()
        held = threading.Event()
        release = threading.Event()

        def worker():
            barrier.wait()
            try:
                item = quota.reserve("parallel", "same-model", "short", 1)
            except quota.QuotaAdmissionDenied:
                return
            with lock:
                admitted.append(item)
            held.set()
            release.wait(timeout=1)
            item.release()

        with patch.dict("os.environ", {"USE_QUOTA_MAX_INFLIGHT_PROVIDER": str(cap), "USE_QUOTA_MAX_INFLIGHT_MODEL": str(cap)}, clear=False):
            threads = [threading.Thread(target=worker) for _ in range(8)]
            for thread in threads:
                thread.start()
            held.wait(timeout=1)
            self.assertLessEqual(quota.snapshot()["active_provider_calls"].get("parallel", 0), cap)
            release.set()
            for thread in threads:
                thread.join(timeout=1)
        self.assertLessEqual(len(admitted), cap)


if __name__ == "__main__":
    unittest.main()
