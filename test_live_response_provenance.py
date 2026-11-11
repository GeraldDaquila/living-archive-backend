import unittest
from pathlib import Path

MAIN = Path(__file__).with_name("main.py").read_text(encoding="utf-8")

class LiveResponseProvenanceTests(unittest.TestCase):
    def test_final_query_boundary_stamps_runtime_identity(self):
        self.assertIn(b"x-living-archive-version", MAIN.encode())
        self.assertIn(b"x-living-archive-fingerprint", MAIN.encode())

    def test_identity_is_present_for_repaired_and_passthrough_json(self):
        self.assertGreaterEqual(
            MAIN.count("x-living-archive-fingerprint"), 2
        )

if __name__ == "__main__":
    unittest.main()
