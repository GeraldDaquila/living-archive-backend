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
def blob_sha1(data): return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def main():
    for rel, expected in PROTECTED.items():
        assert blob_sha1((ROOT/rel).read_bytes())==expected
    main_source=(ROOT/"main.py").read_text()
    ast.parse(main_source)
    assert 'APP_VERSION = "v487.88"' in main_source
    assert 'claims = _normalize_shared_claims_for_use(docs or [])' in main_source
    assert 'synthesis = _build_shared_synthesis_material_for_use(claims)' in main_source
    assert 'claims_for_composition = _legacy_claims_from_synthesis(synthesis, claims)' in main_source
    assert 'build_synthesis_material as _shared_build_synthesis_material' in main_source
    print("v487.88 synthesis hardening QA: PASS")
if __name__=="__main__": raise SystemExit(main())
