"""Current USE repository guard."""
from __future__ import annotations
import hashlib
from pathlib import Path
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
LEGACY_WORKFLOWS = (
    ".github/workflows/v335-validation.yml",
    ".github/workflows/v336-validation.yml",
    ".github/workflows/v337-recommendation-authority-boundary.yml",
    ".github/workflows/v338-asgi-import-validation.yml",
    ".github/workflows/v338-validation.yml",
    ".github/workflows/v339-full-validation.yml",
    ".github/workflows/v340-full-validation.yml",
    ".github/workflows/v387-authority-validation.yml",
)
def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()
def validate_protected_assets() -> list[str]:
    errors=[]
    for rel, expected in PROTECTED.items():
        path=ROOT/rel
        if not path.is_file():
            errors.append(f"missing protected asset: {rel}"); continue
        actual=git_blob_sha1(path.read_bytes())
        if actual != expected:
            errors.append(f"protected asset changed: {rel} expected={expected} actual={actual}")
    return errors
def validate_legacy_workflow_cleanup() -> list[str]:
    return [f"legacy workflow still present: {rel}" for rel in LEGACY_WORKFLOWS if (ROOT/rel).exists()]
def main() -> int:
    errors=validate_protected_assets()+validate_legacy_workflow_cleanup()
    if errors:
        for e in errors: print(f"FAIL: {e}")
        return 1
    print("USE repository guard: PASS")
    return 0
if __name__ == "__main__": raise SystemExit(main())
