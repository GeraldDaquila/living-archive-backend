from pathlib import Path
import ast
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

def blob_sha1(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main():
    for rel, expected in PROTECTED.items():
        assert blob_sha1((ROOT / rel).read_bytes()) == expected
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    primitive = (ROOT / "shared_intelligence_primitives.py").read_text(encoding="utf-8")
    ast.parse(main_source)
    ast.parse(primitive)
    assert 'APP_VERSION = "v487.88"' in main_source
    assert "build_synthesis_material as _shared_build_synthesis_material" in main_source
    assert "def _build_shared_synthesis_material_for_use(claims):" in main_source
    assert "synthesis = _build_shared_synthesis_material_for_use(claims)" in main_source
    assert "def build_synthesis_material(" in primitive
    assert "shared_intelligence_primitives" not in (ROOT / "use_core.py").read_text(encoding="utf-8")
    assert "shared_intelligence_primitives" not in (ROOT / "main_v487_28_runtime.py").read_text(encoding="utf-8")
    print("v487.88 synthesis material seam compatibility QA: PASS")
    print("protected assets: PASS")
    print("shared evidence/claim seams: PASS")
    print("shared synthesis seam: PASS")
    print("orchestration boundaries: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
