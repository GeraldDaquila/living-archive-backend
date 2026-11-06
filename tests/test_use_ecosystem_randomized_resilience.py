"""Seeded synthetic resilience checks across active USE capability boundaries.

No network calls, provider credentials, visitor data, or Pinecone quota are used.
These tests exercise contracts and deterministic routing primitives; they are not
a substitute for live visitor-facing E2E acceptance.
"""
import random
import unittest

import main
import guide_runtime
from pinecone_retrieval_budget import BoundedPineconeIndex
from specialist_registry import available_specialists, build_specialist_request


class FakeIndex:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def query(self, **kwargs):
        self.calls.append(dict(kwargs))
        if self.error:
            raise self.error
        return {"matches": [{"id": str(i)} for i in range(kwargs["top_k"])]}


class RandomizedEcosystemResilienceTests(unittest.TestCase):
    def test_runtime_integration_inventory_is_explicit_and_consistent(self):
        report = main.ecosystem_integration_audit()
        self.assertEqual(report["audit_contract"], "ecosystem-integration-audit-v1")
        self.assertTrue(report["version"])
        self.assertTrue(report["fingerprint"])
        self.assertIsInstance(report["capability_registry"], list)
        self.assertIsInstance(report["runtime_adapters"], list)
        self.assertIsInstance(report["direct_handoffs"], dict)
        self.assertIn("catalogue", report["direct_handoffs"])
        self.assertIn("navigator", report["direct_handoffs"])
        self.assertIn("fsd", report["direct_handoffs"])
        self.assertIn("systems_ph", report["direct_handoffs"])

    def test_all_declared_available_specialists_build_valid_request_envelopes(self):
        capabilities = available_specialists()
        self.assertGreaterEqual(len(capabilities), 5)
        for capability in capabilities:
            with self.subTest(specialist=capability.specialist_id):
                payload = build_specialist_request(
                    request_id="synthetic-resilience-001",
                    guide_version=main.APP_VERSION,
                    specialist_id=capability.specialist_id,
                    original_question="Synthetic test input; no real visitor data.",
                    recognized_territory=capability.trigger_territory,
                    processing_purpose="contract-resilience-test",
                )
                self.assertEqual(payload["specialist_id"], capability.specialist_id)
                self.assertEqual(payload["contract_version"], "v1")
                self.assertEqual(payload["request_id"], "synthetic-resilience-001")

    def test_seeded_randomized_intent_inputs_remain_deterministic(self):
        rng = random.Random(489311)
        samples = [
            ("conceptual", "What is stewardship and why does it matter?"),
            ("navigation", "Where can I find the Guide's essays on governance?"),
            ("lived", "I feel overwhelmed by a recurring conflict with my partner."),
            ("recommendation", "What should I read about discernment?"),
            ("risk", "I am thinking about suicide and may hurt myself."),
            ("ai_truth", "How can I know what is true in the age of AI?"),
        ]
        expanded = []
        for _ in range(120):
            label, query = rng.choice(samples)
            prefix = rng.choice(["", "Please help me: ", "I want to understand: "])
            expanded.append((label, prefix + query))
        for label, query in expanded:
            with self.subTest(label=label, query=query):
                first = guide_runtime._inquiry_profile(query)
                second = guide_runtime._inquiry_profile(query)
                self.assertEqual(first, second)
                self.assertIn(first["action"], {
                    "risk", "recommendation", "navigation", "lived",
                    "foundation", "conceptual", "core"
                })
                if label == "risk":
                    self.assertTrue(first["risk"])
                    self.assertEqual(first["action"], "risk")

    def test_pinecone_proxy_clamps_requests_and_propagates_non_quota_faults(self):
        fake = FakeIndex()
        proxy = BoundedPineconeIndex(fake, per_query_cap=7)
        result = proxy.query(vector=[0.0] * 384, top_k=100)
        self.assertEqual(len(result["matches"]), 7)
        self.assertEqual(fake.calls[0]["top_k"], 7)

        failing = BoundedPineconeIndex(FakeIndex(TimeoutError("synthetic timeout")))
        with self.assertRaises(TimeoutError):
            failing.query(vector=[0.0] * 384, top_k=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
