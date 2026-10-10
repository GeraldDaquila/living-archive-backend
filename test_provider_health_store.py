import unittest
from unittest.mock import patch

from provider_health_store import export_health_states, merge_health_state, save_remote_states
import provider_bank


class ProviderHealthStoreTests(unittest.TestCase):
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

    def test_missing_credentials_fails_closed_without_network(self):
        with patch("provider_health_store._configuration", return_value=("", "")):
            self.assertFalse(save_remote_states({}))


if __name__ == "__main__":
    unittest.main()
