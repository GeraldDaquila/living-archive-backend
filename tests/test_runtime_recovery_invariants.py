"""Regression tests for USE runtime identity and recovery invariants."""
import unittest
import main

class RuntimeRecoveryTests(unittest.TestCase):
    def test_runtime_identity_is_complete_and_consistent(self):
        self.assertTrue(str(main.APP_VERSION).startswith("v"))
        self.assertTrue(main.DEPLOYMENT_FINGERPRINT.startswith("USE-"+main.APP_VERSION+"-"))
        self.assertTrue(main.CANONICAL_BUILD_ID.startswith("USE-BUILD-"+main.APP_VERSION+"-"))
        self.assertEqual(len(main.RUNTIME_SOURCE_SHA256), 64)

    def test_protected_core_integrity_is_enforced_at_import(self):
        # main.py raises during import if the protected runtime manifest drifts.
        self.assertTrue(hasattr(main, "_base"))
        self.assertEqual(main._base._core_runtime_sha, main.EXPECTED_CORE_BLOB_SHA)

    def test_registry_diagnostic_contract_is_non_secret(self):
        state=main.guide_node_registry_state()
        self.assertIn("state", state)
        self.assertIn("failure_count", state)
        self.assertNotIn("authorization", state)

if __name__=="__main__":
    unittest.main()
