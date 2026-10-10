import unittest
from unittest.mock import patch

from provider_health_store import export_health_states, merge_health_state, save_remote_states


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

    def test_missing_credentials_fails_closed_without_network(self):
        with patch("provider_health_store._configuration", return_value=("", "")):
            self.assertFalse(save_remote_states({}))


if __name__ == "__main__":
    unittest.main()
