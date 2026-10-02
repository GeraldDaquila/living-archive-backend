from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]

PROTECTED = {
    "use_core.py": "fb3208a8d287f16562ffd640d89f65d5e8d18607",
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

    primitive = (ROOT / "shared_intelligence_primitives.py").read_text(encoding="utf-8")
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")

    assert "def normalize_claims" in primitive
    assert "def _extract_claims" not in main_source
    assert "normalize_claims as _shared_normalize_claims" in main_source
    assert 'claims = _normalize_shared_claims_for_use(docs or [])' in main_source
    assert 'def _normalize_shared_claims_for_use(candidates):' in main_source
    print("v487.86 claim normalization seam QA: PASS")
    print("protected assets: PASS")
    print("production claim seam: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
