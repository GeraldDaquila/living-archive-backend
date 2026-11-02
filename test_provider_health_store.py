import unittest
import threading
import time
from unittest.mock import patch

import provider_health_store
from provider_health_store import TIMEOUT_SECONDS, export_health_states, merge_health_state, save_remote_states
import provider_bank
import provider_gateway_service


class ProviderHealthStoreTests(unittest.TestCase):
    def test_shared_health_bridge_timeout_cannot_consume_inference_budget(self):
        self.assertLessEqual(TIMEOUT_SECONDS, 0.3)

    def test_guide_preserves_five_time_budgeted_fallback_candidates(self):
        self.assertEqual(provider_bank.GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES, 5)
        self.assertEqual(provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS, 18.0)

    def test_newer_remote_failure_opens_local_state(self):
        local = {"provider": "groq", "model": "model-a", "state": "healthy", "last_failure": 0, "last_success": 10, "failures": 0, "consecutive_failures": 0, "cooldown_until": 0, "quarantine_until": 0}
        remote = {"provider": "groq", "model": "model-a", "state": "open", "last_failure": 20, "last_success": 10, "failures": 1, "consecutive_failures": 1, "cooldown_until": 100, "quarantine_until": 0, "last_error": "429", "category": "rate_limited"}
        merge_health_state(local, remote, now=30)
        self.assertEqual(local["state"], "open")
        self.assertEqual(local["last_failure"], 20)
        self.assertEqual(local["category"], "rate_limited")

    def test_newer_success_clears_stale_quarantine(self):
        local = {"provider": "gemini", "model": "model-b", "state": "open", "last_failure": 20, "last_success": 10, "failures": 1, "consecutive_failures": 1, "cooldown_until": 100, "quarantine_until": 0, "last_error": "429", "category": "rate_limited"}
        remote = {"provider": "gemini", "model": "model-b", "state": "healthy", "last_failure": 20, "last_success": 30, "failures": 1, "consecutive_failures": 0, "cooldown_until": 0, "quarantine_until": 0, "last_error": "", "category": ""}
        merge_health_state(local, remote, now=31)
        self.assertEqual(local["state"], "healthy")
        self.assertEqual(local["consecutive_failures"], 0)
        self.assertEqual(local["cooldown_until"], 0)

    def test_export_never_persists_probe_ownership(self):
        states = {"groq:model-a": {"provider": "groq", "model": "model-a", "state": "half_open", "probe_in_flight": True, "last_failure": 10}}
        exported = export_health_states(states)
        self.assertFalse(exported["groq:model-a"]["probe_in_flight"])

    def test_quality_cooldown_clears_only_after_newer_valid_success(self):
        local = {
            "provider": "groq", "model": "model-c",
            "state": "healthy", "last_failure": 0, "last_success": 20,
            "last_quality_failure": 30, "last_quality_success": 10,
            "quality_failures": 2, "quality_cooldown_until": 330,
            "quality_error": "prescriptive-language",
        }
        remote = {
            "provider": "groq", "model": "model-c",
            "state": "healthy", "last_failure": 0, "last_success": 20,
            "last_quality_failure": 30, "last_quality_success": 40,
            "quality_failures": 0, "quality_cooldown_until": 0,
            "quality_error": "",
        }
        merge_health_state(local, remote, now=41)
        self.assertEqual(local["quality_failures"], 0)
        self.assertEqual(local["quality_cooldown_until"], 0)
        self.assertEqual(local["quality_error"], "")

    def test_repeated_contract_rejections_trigger_quality_cooldown(self):
        state = {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}}
        with patch.object(provider_bank, "_STATE", state), patch.object(provider_bank, "_persist_shared_state"), patch("provider_bank.time.time", side_effect=[100.0, 101.0]):
            provider_bank._record_quality_rejection("test", "model", "hrn_relational", "prescriptive-language")
            provider_bank._record_quality_rejection("test", "model", "hrn_relational", "prescriptive-language")
        model_state = state["quality"]["quality:hrn_relational:test:model"]
        self.assertEqual(model_state["quality_failures"], 2)
        self.assertEqual(model_state["quality_cooldown_until"], 401.0)

    def test_quality_cooldown_excludes_candidate(self):
        state = {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}}
        blocked_model = provider_bank.new_state("groq", "model-a")
        blocked_model["quality_failures"] = 2
        blocked_model["quality_cooldown_until"] = provider_bank.time.time() + 300
        state["models"]["groq:model-a"] = blocked_model
        state["quality"]["quality:generic:groq:model-a"] = {"provider": "groq", "model": "model-a", "operation": "generic", "quality_failures": 2, "last_quality_failure": 1, "last_quality_success": 0, "quality_cooldown_until": blocked_model["quality_cooldown_until"], "quality_error": "prescriptive-language"}
        with patch.object(provider_bank, "_STATE", state), \
             patch.object(provider_bank, "_configured", return_value={"groq": ["model-a", "model-b"]}), \
             patch.object(provider_bank, "_eligible", return_value=(True, [])), \
             patch.object(provider_bank, "_capabilities", return_value=frozenset({"json_object"})):
            candidates = provider_bank.candidates(None, operation="generic")
        self.assertEqual([item["model"] for item in candidates], ["model-b"])

    def test_groq_model_daily_token_limit_uses_provider_retry_window(self):
        state = {
            "models": {
                "groq:openai/gpt-oss-20b": provider_bank.new_state("groq", "openai/gpt-oss-20b"),
                "groq:openai/gpt-oss-120b": provider_bank.new_state("groq", "openai/gpt-oss-120b"),
            },
            "quality": {},
            "provider_cursor": 0,
            "model_cursors": {},
        }
        message = (
            "Error code: 429 - Rate limit reached for model "
            "`openai/gpt-oss-20b` on tokens per day (TPD). "
            "Please try again in 9m47.088s."
        )
        exc = provider_bank.ProviderCallError(message, "groq", "openai/gpt-oss-20b")
        with patch.object(provider_bank, "_STATE", state), \
             patch.object(provider_bank, "_persist_shared_state"), \
             patch("provider_bank.time.time", return_value=1000.0):
            provider_bank._failure(exc, "groq", "openai/gpt-oss-20b")
        limited = state["models"]["groq:openai/gpt-oss-20b"]
        sibling = state["models"]["groq:openai/gpt-oss-120b"]
        self.assertEqual(limited["category"], "rate_limited")
        self.assertAlmostEqual(limited["cooldown_until"], 1587.088, places=3)
        self.assertEqual(sibling["state"], "healthy")
        self.assertEqual(sibling["category"], "")

    def test_provider_gateway_uses_shared_parser_for_fenced_json(self):
        def fake_route(**kwargs):
            parsed = kwargs["parse"]('```json\n{"response":"A complete response."}\n```')
            return {
                "parsed": parsed,
                "provider": "workers_ai",
                "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                "preference_order": [],
            }

        with patch.object(provider_gateway_service, "provider_bank_route", side_effect=fake_route):
            result = provider_gateway_service.execute(
                operation="hrn_relational",
                messages=[{"role": "user", "content": "Return a JSON response."}],
                max_tokens=300,
                use_core=object(),
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["response"], "A complete response.")

    def test_cloudflare_credentials_trim_whitespace(self):
        with patch.dict("os.environ", {
            "CLOUDFLARE_API_TOKEN": "  token-value\n",
            "CLOUDFLARE_ACCOUNT_ID": " account-id ",
        }, clear=False):
            token, account = provider_bank._cloudflare_credentials()
        self.assertEqual(token, "token-value")
        self.assertEqual(account, "account-id")

    def test_workers_ai_model_path_preserves_route_segments(self):
        url = provider_bank._workers_url("account-id", "@cf/zai-org/glm-4.7-flash")
        self.assertEqual(
            url,
            "https://api.cloudflare.com/client/v4/accounts/account-id/ai/run/@cf/zai-org/glm-4.7-flash",
        )

    def test_workers_ai_account_id_is_encoded_as_one_path_segment(self):
        url = provider_bank._workers_url("account/id", "@cf/google/gemma-4-26b-a4b-it")
        self.assertIn(
            "/accounts/account%2Fid/ai/run/@cf/google/gemma-4-26b-a4b-it",
            url,
        )

    def test_workers_ai_extracts_openai_compatible_message_content(self):
        self.assertEqual(
            provider_bank._workers_extract_text({"choices": [{"message": {"content": "A useful response."}}]}),
            "A useful response.",
        )

    def test_workers_ai_extracts_nested_text_chunks(self):
        self.assertEqual(
            provider_bank._workers_extract_text({"response": [{"text": "First"}, {"text": "Second"}]}),
            "First\\nSecond",
        )

    def test_workers_ai_empty_response_diagnostic_contains_shape_only(self):
        diagnostic = provider_bank._workers_response_diagnostic({"result": {"response": "", "metadata": {"x": 1}}})
        self.assertEqual(diagnostic["response_chars"], 0)
        self.assertEqual(diagnostic["result_keys"], ["metadata", "response"])
        self.assertNotIn("A useful response.", str(diagnostic))

    def test_workers_ai_fast_fallback_has_json_composition_capabilities(self):
        capabilities = provider_bank._capabilities(
            "workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        )
        self.assertTrue({
            "json_object", "json_schema_best_effort", "text_generation",
            "long_context", "composition", "relational_analysis", "low_latency",
        }.issubset(capabilities))

    def test_workers_ai_fast_fallback_is_retained_with_explicit_model_list(self):
        from types import SimpleNamespace
        with patch.dict("os.environ", {
            "CLOUDFLARE_API_TOKEN": "token",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "USE_WORKERS_AI_MODELS": "@cf/google/gemma-4-26b-a4b-it,@cf/zai-org/glm-4.7-flash",
        }, clear=True):
            configured = provider_bank._configured(SimpleNamespace(get_live_groq_models=lambda: []))
        self.assertEqual(configured["workers_ai"], [
            "@cf/google/gemma-4-26b-a4b-it",
            "@cf/zai-org/glm-4.7-flash",
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        ])

    def test_workers_ai_disables_gemma_thinking_for_latency(self):
        with patch.object(provider_bank, "_http_json", return_value={"result": {"response": "ok"}}) as request:
            result = provider_bank._workers(
                "token", "account-id", "@cf/google/gemma-4-26b-a4b-it",
                [{"role": "user", "content": "Return ok"}], 40,
            )
        self.assertEqual(result, "ok")
        self.assertEqual(request.call_args.args[2]["chat_template_kwargs"], {"enable_thinking": False})

    def test_workers_ai_uses_bounded_extended_inference_timeout(self):
        with patch.object(provider_bank, "_http_json", return_value={"result": {"response": "ok"}}) as request:
            result = provider_bank._workers(
                "token", "account-id", "@cf/zai-org/glm-4.7-flash",
                [{"role": "user", "content": "Return ok"}], 40,
            )
        self.assertEqual(result, "ok")
        self.assertEqual(request.call_args.kwargs.get("timeout"), 12)

    def test_successful_shared_health_read_is_cached_briefly(self):
        with patch.object(provider_health_store, "_READ_CACHE", None), \
             patch.object(provider_health_store, "_READ_CACHE_UNTIL", 0.0), \
             patch.object(provider_health_store, "_READ_IN_FLIGHT", None), \
             patch.object(provider_health_store, "_READ_IN_FLIGHT_RESULT", None), \
             patch.object(provider_health_store, "_request", return_value={
                 "contract_version": "v2",
                 "states": {"groq:model-a": {"provider": "groq", "model": "model-a", "state": "healthy"}},
             }) as request:
            first = provider_health_store.load_remote_states()
            second = provider_health_store.load_remote_states()
        self.assertEqual(first, second)
        request.assert_called_once_with("GET")

    def test_concurrent_cold_reads_share_one_bridge_attempt(self):
        with patch.object(provider_health_store, "_READ_CACHE", None), \
             patch.object(provider_health_store, "_READ_CACHE_UNTIL", 0.0), \
             patch.object(provider_health_store, "_READ_IN_FLIGHT", None), \
             patch.object(provider_health_store, "_READ_IN_FLIGHT_RESULT", None), \
             patch.object(provider_health_store, "_request", side_effect=lambda method: (
                 time.sleep(0.05) or {
                     "contract_version": "v2",
                     "states": {"groq:model-a": {"provider": "groq", "model": "model-a", "state": "healthy"}},
                 }
             )) as request:
            results = []
            threads = [threading.Thread(target=lambda: results.append(provider_health_store.load_remote_states())) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        request.assert_called_once_with("GET")
        self.assertEqual(len(results), 8)
        self.assertTrue(all(result and "groq:model-a" in result for result in results))

    def test_request_serialization_failure_does_not_leak_transport_slot(self):
        slot = threading.BoundedSemaphore(1)
        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")), \
             patch.object(provider_health_store, "_REQUEST_SLOT", slot), \
             patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0), \
             patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False), \
             patch.object(provider_health_store, "urlopen") as request:
            result = provider_health_store._request("POST", {"not_json_safe": object()})
            self.assertIsNone(result)
            request.assert_not_called()
            # Request preparation failed before reserving the only worker slot.
            self.assertTrue(slot.acquire(blocking=False))
            slot.release()

    def test_total_deadline_bounds_a_stalled_transport_worker(self):
        started = threading.Event()
        release = threading.Event()
        finished = threading.Event()
        slot = threading.BoundedSemaphore(1)

        def stalled_transport(*args, **kwargs):
            started.set()
            release.wait(1.0)
            finished.set()
            raise TimeoutError("simulated stalled transport")

        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")), \
             patch.object(provider_health_store, "_REQUEST_SLOT", slot), \
             patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0), \
             patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False), \
             patch.object(provider_health_store, "urlopen", side_effect=stalled_transport):
            before = time.monotonic()
            result = provider_health_store._request("GET")
            elapsed = time.monotonic() - before
            self.assertIsNone(result)
            self.assertTrue(started.is_set())
            self.assertLess(elapsed, TIMEOUT_SECONDS + 0.15)
            # The worker is bounded to one outstanding slot and is daemonized.
            release.set()
            self.assertTrue(finished.wait(0.5))

    def test_pre_deadline_result_is_not_lost_before_completion_event_signal(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class ReleaseBarrierSlot:
            def __init__(self):
                self.inner = threading.BoundedSemaphore(1)
                self.release_entered = threading.Event()
                self.allow_release = threading.Event()

            def acquire(self, blocking=False):
                return self.inner.acquire(blocking=blocking)

            def release(self):
                self.release_entered.set()
                if not self.allow_release.wait(1.0):
                    raise AssertionError("test did not release transport slot")
                self.inner.release()

        slot = ReleaseBarrierSlot()
        body = b'{"contract_version":"v2","success":true,"submitted":1,"written":1}'
        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")), \\
             patch.object(provider_health_store, "_REQUEST_SLOT", slot), \\
             patch.object(provider_health_store, "TIMEOUT_SECONDS", 0.05), \\
             patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0), \\
             patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False), \\
             patch.object(provider_health_store, "urlopen", return_value=FakeResponse()), \\
             patch.object(provider_health_store, "_read_response_body", return_value=body):
            result_holder = {}

            def call():
                result_holder["result"] = provider_health_store._request(
                    "POST", {"contract_version": "v2", "states": {"groq:model-a": {}}}
                )

            worker = threading.Thread(target=call)
            worker.start()
            self.assertTrue(slot.release_entered.wait(0.5))
            worker.join(timeout=0.5)
            try:
                self.assertFalse(worker.is_alive())
                self.assertEqual(result_holder.get("result"), {
                    "contract_version": "v2",
                    "success": True,
                    "submitted": 1,
                    "written": 1,
                })
            finally:
                slot.allow_release.set()

    def test_response_completed_after_absolute_deadline_is_discarded(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        slot = threading.BoundedSemaphore(1)

        def late_body(*args, **kwargs):
            time.sleep(0.04)
            return b'{"contract_version":"v2","states":{}}'

        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")), \
             patch.object(provider_health_store, "_REQUEST_SLOT", slot), \
             patch.object(provider_health_store, "TIMEOUT_SECONDS", 0.01), \
             patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0), \
             patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False), \
             patch.object(provider_health_store, "urlopen", return_value=FakeResponse()), \
             patch.object(provider_health_store, "_read_response_body", side_effect=late_body):
            result = provider_health_store._request("GET")
            self.assertIsNone(result)
            # Wait for the intentionally late daemon worker to release its slot.
            deadline = time.monotonic() + 0.5
            while True:
                if slot.acquire(blocking=False):
                    slot.release()
                    break
                if time.monotonic() >= deadline:
                    self.fail("transport worker did not release its bounded slot")
                time.sleep(0.005)
        # The response became available after the caller's absolute deadline;
        # it must not be accepted on a scheduling race.

    def test_stalled_transport_slot_prevents_worker_backlog(self):
        slot = threading.BoundedSemaphore(1)
        self.assertTrue(slot.acquire(blocking=False))
        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")), \
             patch.object(provider_health_store, "_REQUEST_SLOT", slot), \
             patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0), \
             patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False), \
             patch.object(provider_health_store, "urlopen") as request:
            before = time.monotonic()
            result = provider_health_store._request("GET")
            self.assertIsNone(result)
            self.assertLess(time.monotonic() - before, 0.05)
            request.assert_not_called()
        slot.release()

    def test_missing_credentials_fails_closed_without_network(self):
        with patch("provider_health_store._configuration", return_value=("", "")):
            self.assertFalse(save_remote_states({}))



    def test_singleflight_waiter_does_not_outwait_shared_health_http_budget(self):
        entered = threading.Event()
        release = threading.Event()
        waiter_done = threading.Event()

        def slow_request(method):
            entered.set()
            release.wait(timeout=2.0)
            return None

        with patch.object(provider_health_store, "_READ_CACHE", None), \
             patch.object(provider_health_store, "_READ_CACHE_UNTIL", 0.0), \
             patch.object(provider_health_store, "_READ_IN_FLIGHT", None), \
             patch.object(provider_health_store, "_READ_IN_FLIGHT_RESULT", None), \
             patch.object(provider_health_store, "_request", side_effect=slow_request):
            owner = threading.Thread(target=provider_health_store.load_remote_states)
            owner.start()
            self.assertTrue(entered.wait(timeout=1.0))

            def wait_for_owner():
                provider_health_store.load_remote_states()
                waiter_done.set()

            waiter = threading.Thread(target=wait_for_owner)
            waiter.start()
            completed_within_bound = waiter_done.wait(timeout=provider_health_store.TIMEOUT_SECONDS + 0.08)
            release.set()
            waiter.join(timeout=1.0)
            owner.join(timeout=1.0)

        self.assertTrue(completed_within_bound)
        self.assertFalse(owner.is_alive())
        self.assertFalse(waiter.is_alive())


    def test_shared_health_read_enforces_total_wall_clock_deadline_on_trickle_body(self):
        from types import SimpleNamespace

        clock = SimpleNamespace(value=10.0)

        class FakeSocket:
            def __init__(self):
                self.timeouts = []

            def settimeout(self, value):
                self.timeouts.append(value)

        class TrickleResponse:
            def __init__(self):
                self.parts = [b'{"contract_version":', b'"v2",', b'"states":{}}']
                self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=FakeSocket()))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read1(self, size):
                clock.value += 0.10
                return self.parts.pop(0) if self.parts else b""

        response = TrickleResponse()
        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")):
            with patch.object(provider_health_store, "_monotonic", side_effect=lambda: clock.value):
                with patch.object(provider_health_store, "urlopen", return_value=response) as request:
                    with patch.object(provider_health_store.time, "monotonic", return_value=10.0):
                        with patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0):
                            with patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False):
                                result = provider_health_store._request("GET")

        self.assertIsNone(result)
        request.assert_called_once()
        self.assertTrue(response.fp.raw._sock.timeouts)
        self.assertTrue(all(value <= provider_health_store.TIMEOUT_SECONDS for value in response.fp.raw._sock.timeouts))

    def test_shared_health_read_accepts_complete_body_within_total_deadline(self):
        from types import SimpleNamespace

        clock = SimpleNamespace(value=20.0)

        class FakeSocket:
            def settimeout(self, value):
                self.timeout = value

        class FastResponse:
            def __init__(self):
                self.parts = [b'{"contract_version":"v2",', b'"states":{}}']
                self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=FakeSocket()))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read1(self, size):
                clock.value += 0.04
                return self.parts.pop(0) if self.parts else b""

        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")):
            with patch.object(provider_health_store, "_monotonic", side_effect=lambda: clock.value):
                with patch.object(provider_health_store, "urlopen", return_value=FastResponse()):
                    with patch.object(provider_health_store.time, "monotonic", return_value=20.0):
                        with patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0):
                            with patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False):
                                result = provider_health_store._request("GET")

        self.assertEqual(result, {"contract_version": "v2", "states": {}})


    def test_shared_health_read_accepts_buffered_body_without_live_socket_reference(self):
        from types import SimpleNamespace

        clock = SimpleNamespace(value=30.0)

        class BufferedResponse:
            def __init__(self):
                self.parts = [b'{"contract_version":"v2",', b'"states":{}}']
                # urllib can retain readable buffered bytes after detaching
                # the underlying socket reference.
                self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=None))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read1(self, size):
                clock.value += 0.02
                return self.parts.pop(0) if self.parts else b""

        response = BufferedResponse()
        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")):
            with patch.object(provider_health_store, "_monotonic", side_effect=lambda: clock.value):
                with patch.object(provider_health_store, "urlopen", return_value=response):
                    with patch.object(provider_health_store.time, "monotonic", return_value=30.0):
                        with patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0):
                            with patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False):
                                result = provider_health_store._request("GET")

        self.assertEqual(result, {"contract_version": "v2", "states": {}})


    def test_incomplete_http_response_fails_closed_without_escaping(self):
        from http.client import IncompleteRead

        with patch.object(provider_health_store, "_configuration", return_value=("https://health.invalid/state", "test-secret")), \
             patch.object(provider_health_store, "urlopen", side_effect=IncompleteRead(b'{"contract', 20)), \
             patch.object(provider_health_store, "_CIRCUIT_OPEN_UNTIL", 0.0), \
             patch.object(provider_health_store, "_CIRCUIT_PROBE_IN_FLIGHT", False):
            result = provider_health_store._request("GET")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
