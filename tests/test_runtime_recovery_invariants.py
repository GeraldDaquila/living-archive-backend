"""Static regression tests for USE runtime identity and recovery contracts."""
import ast
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "main.py"

class RuntimeRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MAIN.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_runtime_identity_contract_is_declared(self):
        for symbol in ("APP_VERSION", "DEPLOYMENT_FINGERPRINT", "CANONICAL_BUILD_ID", "RUNTIME_SOURCE_SHA256"):
            self.assertIn(symbol, self.source)

    def test_protected_core_boundary_is_declared(self):
        self.assertIn("EXPECTED_CORE_BLOB_SHA", self.source)
        self.assertIn("_StrictCorsBoundary", self.source)

    def test_cors_boundary_is_outer_and_origin_bounded(self):
        self.assertIn("https://geralddaquila.com", self.source)
        self.assertIn("https://www.geralddaquila.com", self.source)
        self.assertIn("app = _StrictCorsBoundary(app)", self.source)

if __name__=="__main__":
    unittest.main()
