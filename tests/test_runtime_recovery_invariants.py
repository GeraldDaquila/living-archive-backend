"""Regression tests for USE runtime identity and recovery invariants."""
import unittest
import main

class RuntimeRecoveryTests(unittest.TestCase):
    def test_runtime_identity_is_complete_and_consistent(self):
        self.assertEqual(main.APP_VERSION, "v489.310")
        self.assertTrue(main.DEPLOYMENT_FINGERPRINT.startswith("USE-"+main.APP_VERSION+"-"))
        self.assertTrue(main.CANONICAL_BUILD_ID.startswith("USE-BUILD-"+main.APP_VERSION+"-"))
        self.assertEqual(len(main.RUNTIME_SOURCE_SHA256), 64)

    def test_protected_core_manifest_matches_loaded_core(self):
        self.assertEqual(getattr(main._base, "_core_runtime_sha", ""), main.EXPECTED_CORE_BLOB_SHA)

    def test_registry_state_is_non_secret_and_bounded(self):
        state=main.guide_node_registry_state()
        self.assertIn(state.get("state"), ("fresh","stale","unavailable"))
        self.assertIn("failure_count", state)
        self.assertNotIn("authorization", state)

if __name__=="__main__":
    unittest.main()
