"""Structural QA for v487.82 implementation archaeology.

Verifies that the archaeology checkpoint names only existing production
functions and preserves the protected runtime boundary.
"""
from __future__ import annotations

from pathlib import Path
import ast
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]

PROTECTED = {
    "use_core.py": "fb3208a8d287f16562ffd640d89f65d5e8d18607",
    "main.py": "6a2d4b746020d6086bf1b997753894257c3be96c",
    "main_v487_28_runtime.py": "4c8c72d70fa5f93e8bbcdd1c1d8e4696a4949a31",
    "specialist_registry.py": "9c18aca2c47333355ba87c650af32f9b43e2f716",
    "specialist_adapters.py": "ff27c9e7c6df66c622cf389765c7fed775810383",
    "relationship_contribution.py": "6298564273f9d9cbc43d0f6cea22a2f8568506a9",
    "relationship_adapter.py": "c10a26e2f4432a0b7712dbc17e8acca4a76c17c5",
}


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


EXPECTED_FUNCTIONS = (
    "_weighted_inquiry_profile",
    "_inquiry_profile",
    "_candidate_sentences",
    "_extract_claims",
    "_build_factual_answer",
    "_build_lived_experience_answer",
    "_recommendation_answer",
    "_unified_visitor_construction",
    "_v487_generate_boundary",
    "_v487_evidence_gap_boundary",
    "_sanitize_visitor_output",
)


def main() -> int:
    for rel, expected in PROTECTED.items():
        actual = blob_sha1((ROOT / rel).read_bytes())
        assert actual == expected, (rel, expected, actual)

    runtime = (ROOT / "main_v487_28_runtime.py").read_text(encoding="utf-8")
    for name in EXPECTED_FUNCTIONS:
        assert re.search(rf"\bdef\s+{re.escape(name)}\b", runtime), name

    report = (ROOT / "QA" / "IMPLEMENTATION_ARCHAEOLOGY.md").read_text(encoding="utf-8")
    ast.parse((ROOT / "QA" / "IMPLEMENTATION_ARCHAEOLOGY.py").read_text(encoding="utf-8"))
    required = (
        "data-first and transformation-first",
        "not extraction",
        "use_core.py",
        "general_utility.py",
    )
    for marker in required:
        assert marker in report, marker

    print("v487.82 implementation archaeology QA: PASS")
    print("protected production assets: PASS")
    print("mapped USE functions: PASS")
    print("production extraction/wiring: ABSENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
