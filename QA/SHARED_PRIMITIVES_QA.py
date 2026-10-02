"""Structural QA for the v487.83 isolated primitive draft."""
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

    primitive = ROOT / "shared_intelligence_primitives.py"
    tests = ROOT / "QA" / "SHARED_PRIMITIVES_TESTS.py"
    ast.parse(primitive.read_text(encoding="utf-8"), filename=str(primitive))
    ast.parse(tests.read_text(encoding="utf-8"), filename=str(tests))

    production_files = (
        ROOT / "main.py",
        ROOT / "main_v487_28_runtime.py",
        ROOT / "use_core.py",
        ROOT / "specialist_adapters.py",
        ROOT / "relationship_adapter.py",
        ROOT / "relationship_contribution.py",
    )
    for path in production_files:
        text = path.read_text(encoding="utf-8")
        assert "shared_intelligence_primitives" not in text, path.name

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(tests)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    print("v487.83 shared primitive QA: PASS")
    print("protected production assets: PASS")
    print("primitive isolated from production: PASS")
    print("regression probes: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
