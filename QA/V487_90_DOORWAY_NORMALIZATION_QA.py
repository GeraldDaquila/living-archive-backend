"""Structural QA for the v487.90 doorway candidate normalization primitive."""
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
    source = (ROOT / "shared_intelligence_primitives.py").read_text(encoding="utf-8")
    ast.parse(source, filename="shared_intelligence_primitives.py")
    assert "def normalize_doorway_candidates(" in source
    assert "DoorwayCandidate(" in source
    assert "candidate_rank" in source
    assert "canonical authority" in source
    forbidden = ("pinecone", "groq", "fetch_canonical_context", "select canonical")
    executable = source.split('"""\n')[2] if '"""\n' in source else source
    assert not any(marker.casefold() in executable.casefold() for marker in forbidden)
    # The shared primitive is intentionally independent of the protected runtime.
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "shared_intelligence_primitives" in main_source
    print("v487.90 doorway normalization QA: PASS")

if __name__ == "__main__":
    main()
