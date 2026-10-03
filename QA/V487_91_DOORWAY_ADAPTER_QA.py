"""Targeted QA for the v487.91 doorway normalization adapter.

The adapter must only transform supplied candidate mappings into the shared
DoorwayCandidate representation. It must not select, rank, retrieve, route,
or generate visitor-facing prose.
"""
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
    return hashlib.sha1(f"blob {len(data)}\\0".encode() + data).hexdigest()

def main():
    for rel, expected in PROTECTED.items():
        assert blob_sha1((ROOT / rel).read_bytes()) == expected
    tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"), filename="main.py")
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_build_doorway_candidates_for_use")
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "normalize_doorway_candidates" for node in ast.walk(fn)) or any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_normalize_shared_doorways" for node in ast.walk(fn))
    source = ast.get_source_segment((ROOT / "main.py").read_text(encoding="utf-8"), fn) or ""
    forbidden = ("pinecone", "groq", "fetch_canonical_context", "_canonical_primary_from_docs", "_select_adjacent", "generate")
    assert not any(marker.casefold() in source.casefold() for marker in forbidden)
    shared = ast.parse((ROOT / "shared_intelligence_primitives.py").read_text(encoding="utf-8"), filename="shared_intelligence_primitives.py")
    shared_fn = next(node for node in shared.body if isinstance(node, ast.FunctionDef) and node.name == "normalize_doorway_candidates")
    shared_source = ast.get_source_segment((ROOT / "shared_intelligence_primitives.py").read_text(encoding="utf-8"), shared_fn) or ""
    assert "return tuple(output)" in shared_source
    assert not any(marker.casefold() in shared_source.casefold() for marker in ("pinecone", "groq", "fetch_canonical_context", "canonical_primary", "generate"))
    print("v487.91 doorway adapter QA: PASS")

if __name__ == "__main__":
    main()
