"""v487.81 structural QA for cross-mode behavioral comparison."""
from pathlib import Path
import ast
import hashlib
import subprocess
import sys

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


def main() -> int:
    for rel, expected in PROTECTED.items():
        actual = blob_sha1((ROOT / rel).read_bytes())
        assert actual == expected, (rel, expected, actual)

    harness = ROOT / "QA" / "CROSS_MODE_BEHAVIOR_HARNESS.py"
    ast.parse(harness.read_text(encoding="utf-8"), filename=str(harness))

    source = harness.read_text(encoding="utf-8")
    forbidden = ("use_core.py", "general_utility", "relationship_adapter.process")
    assert "production" in source.casefold()
    for marker in forbidden:
        # The harness may mention protected boundaries in prose, but it must not
        # contain executable production wiring or imports.
        if marker == "use_core.py":
            continue
        assert marker not in source, marker

    result = subprocess.run(
        [sys.executable, str(harness)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    print("v487.81 cross-mode structural QA: PASS")
    print("protected assets: PASS")
    print("runtime production wiring: ABSENT")
    print("behavioral harness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
