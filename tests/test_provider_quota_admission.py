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
        all_attempted = threading.Event()
        release = threading.Event()
        attempts = [0]

        def worker():
            barrier.wait()
            item = None
            try:
                item = quota.reserve("parallel", "same-model", "short", 1)
            except quota.QuotaAdmissionDenied:
                pass
            with lock:
                if item is not None:
                    admitted.append(item)
                attempts[0] += 1
                if attempts[0] == 8:
                    all_attempted.set()
            if item is not None:
                held.set()
                release.wait(timeout=1)
                item.release()

        with patch.dict("os.environ", {"USE_QUOTA_MAX_INFLIGHT_PROVIDER": str(cap), "USE_QUOTA_MAX_INFLIGHT_MODEL": str(cap)}, clear=False):
            threads = [threading.Thread(target=worker) for _ in range(8)]
            for thread in threads:
                thread.start()
            held.wait(timeout=1)
            self.assertTrue(all_attempted.wait(timeout=1))
            self.assertLessEqual(quota.snapshot()["active_provider_calls"].get("parallel", 0), cap)
            release.set()
            for thread in threads:
                thread.join(timeout=1)
        self.assertLessEqual(len(admitted), cap)


    def test_settle_output_refunds_unused_completion_reservation(self):
        with patch.dict(
            "os.environ",
            {
                "USE_QUOTA_TEST_TPM": "10000",
                "USE_QUOTA_TEST_TPD": "100000",
            },
            clear=False,
        ), patch.object(quota, "_monotonic", return_value=0.0):
            reservation = quota.reserve("test", "model-a", "x" * 4000, 4000)
            before_tpm = quota._BUCKETS["test:tpm"]["tokens"]
            before_tpd = quota._BUCKETS["test:tpd"]["tokens"]

            reservation.settle_output(type("Output", (str,), {"completion_tokens": 500})("short output"))

            self.assertEqual(before_tpm, 10000 - reservation.token_estimate)
            self.assertEqual(quota._BUCKETS["test:tpm"]["tokens"], before_tpm + 3500)
            self.assertEqual(quota._BUCKETS["test:tpd"]["tokens"], before_tpd + 3500)
            reservation.release()

    def test_hrn_grounding_accepts_observer_owned_movement_fields(self):
        import json
        import provider_bank as bank

        brief = {
            "observer_intention": "You both want the recurring argument to change.",
            "observer_contrast": "The argument keeps returning despite that shared intention.",
            "observer_so_what": "The wish to improve and the repeated exchange are not yet aligned.",
            "observer_delta": "The focus moves from stated intention to the recurring exchange.",
            "observer_horizon": "The moment the argument begins to repeat.",
            "observer_next_intention": "Notice the point where the familiar exchange returns.",
        }
        messages = [{
            "role": "user",
            "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps(brief),
        }]
        self.assertEqual(
            bank._hrn_question_grounding_violation(
                "What usually happens just before the argument starts again?",
                messages,
            ),
            "",
        )

    def test_hrn_grounding_remains_fail_closed_without_concrete_anchors(self):
        import json
        import provider_bank as bank

        brief = {
            "observer_intention": "",
            "observer_contrast": "",
            "observer_so_what": "",
            "observer_delta": "",
            "observer_horizon": "",
            "observer_next_intention": "",
        }
        messages = [{
            "role": "user",
            "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps(brief),
        }]
        reason = bank._hrn_question_grounding_violation(
            "What happens next?",
            messages,
        )
        self.assertIn("movement brief has no concrete question anchors", reason)



if __name__ == "__main__":
    unittest.main()
