"""Regression: the shared JSON exit is the final authority for Guide navigation."""
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")


class OuterDoorwayAuthorityContractTests(unittest.TestCase):
    def test_archive_claim_is_not_exempt_from_outer_navigation_recovery(self):
        self.assertIn("Single authoritative outer doorway contract", MAIN)
        self.assertNotIn("not _archive_claim_final", MAIN)

    def test_only_explicit_no_doorway_standard_can_suppress_navigation(self):
        self.assertIn('_forbids_doorway = (', MAIN)
        self.assertIn('payload["canonical_doorway"] = None', MAIN)

    def test_outer_boundary_preserves_then_recovers_verified_navigation(self):
        self.assertIn('payload.get("recommendation")', MAIN)
        self.assertIn('payload.get("canonical_doorway")', MAIN)
        self.assertIn("_verified_archive_doorway_fallback(", MAIN)
        self.assertIn("_boundary_canonical_doorway(", MAIN)


if __name__ == "__main__":
    unittest.main()
