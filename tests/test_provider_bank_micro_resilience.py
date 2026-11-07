"""Offline micro-resilience simulation for the USE Provider Bank.

Exercises provider selection and bounded fallback with deterministic synthetic
providers. No network calls, credentials, Pinecone access, or visitor data.
"""
import unittest
from unittest.mock import patch

import provider_bank


class _Core:
    def __init__(self, providers):
        self._providers = providers
    def configured_providers(self):
        return self._providers


class _AdmissionDenied(Exception):
    pass


class ProviderBankMicroResilienceTests(unittest.TestCase):
    def _core(self):
        return _Core({
            "groq": ["openai/gpt-oss-20b"],
            "workers_ai": ["@cf/google/gemma-4-26b-a4b-it"],
            "nvidia": ["nvidia/nemotron-3.5-lightning-30b-a3b"],
        })

    def test_general_guide_fast_failure_reaches_independent_provider(self):
        calls = []
        def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
            calls.append((item["provider"], item["model"]))
            if item["provider"] == "groq":
                raise provider_bank.ProviderCallError("synthetic fast outage", "groq", item["model"], category="network_failure")
            return '{"response":"synthetic success"}'
        with patch.object(provider_bank, "_quota_guarded_call", fake_call),              patch.object(provider_bank, "_sync_shared_state"),              patch.object(provider_bank, "_persist_shared_state"):
            result = provider_bank.route(
                use_core=self._core(),
                messages=[{"role":"user","content":"Synthetic resilience input."}],
                max_tokens=900,
                parse=lambda raw: {"response": str(raw)},
                operation="general_guide_composition",
            )
        self.assertIsNotNone(result)
        self.assertGreaterEqual(len(calls), 2)
        self.assertNotEqual(calls[0][0], calls[1][0])

    def test_quota_admission_denial_does_not_poison_provider_health(self):
        item = {"provider":"groq","model":"openai/gpt-oss-20b"}
        state = provider_bank._state(item["provider"], item["model"])
        before = int(state.get("failures", 0) or 0)
        def fake_call(*args, **kwargs):
            raise provider_bank.QuotaAdmissionDenied(1.0)
        with patch.object(provider_bank, "_quota_guarded_call", fake_call),              patch.object(provider_bank, "_sync_shared_state"),              patch.object(provider_bank, "_persist_shared_state"):
            provider_bank.route(
                use_core=_Core({"groq":["openai/gpt-oss-20b"]}),
                messages=[{"role":"user","content":"Synthetic."}],
                max_tokens=900,
                parse=lambda raw: {"response": raw},
                operation="general_guide_composition",
            )
        self.assertEqual(int(state.get("failures", 0) or 0), before)

    def test_contract_rejection_can_fall_through_to_next_candidate(self):
        calls = []
        def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
            calls.append(item["provider"])
            return "synthetic"
        def parse(raw):
            if len(calls) == 1:
                raise ValueError("invalid JSON")
            return {"response":"recovered"}
        with patch.object(provider_bank, "_quota_guarded_call", fake_call),              patch.object(provider_bank, "_sync_shared_state"),              patch.object(provider_bank, "_persist_shared_state"):
            result = provider_bank.route(
                use_core=self._core(),
                messages=[{"role":"user","content":"Synthetic."}],
                max_tokens=900,
                parse=parse,
                operation="general_guide_composition",
            )
        self.assertIsNotNone(result)
        self.assertGreaterEqual(len(calls), 2)

    def test_exhaustion_returns_none_without_serial_unbounded_walk(self):
        calls = []
        def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
            calls.append(item["provider"])
            raise provider_bank.ProviderCallError("synthetic outage", item["provider"], item["model"], category="timeout")
        with patch.object(provider_bank, "_quota_guarded_call", fake_call),              patch.object(provider_bank, "_sync_shared_state"),              patch.object(provider_bank, "_persist_shared_state"):
            result = provider_bank.route(
                use_core=self._core(),
                messages=[{"role":"user","content":"Synthetic."}],
                max_tokens=900,
                parse=lambda raw: {"response": raw},
                operation="general_guide_composition",
            )
        self.assertIsNone(result)
        self.assertLessEqual(len(calls), 3)

    def test_operation_capability_policy_excludes_ineligible_candidates(self):
        pool = provider_bank.select(
            self._core(),
            operation="general_guide_composition",
            schema=None,
        )
        self.assertTrue(pool)
        required = provider_bank.OPERATION_REQUIREMENTS["general_guide_composition"]
        for item in pool:
            capabilities = provider_bank._capabilities(item["provider"], item["model"])
            self.assertTrue(required.issubset(capabilities))


if __name__ == "__main__":
    unittest.main(verbosity=2)
