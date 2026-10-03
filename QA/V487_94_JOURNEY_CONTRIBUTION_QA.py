from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = {
    "use_core.py": "fb3208a8d287f16562ffd640d89f65d5e8d18607",
    "main_v487_28_runtime.py": "4c8c72d70fa5f93e8bbcdd1c1d8e4696a4949a31",
    "specialist_adapters.py": "ff27c9e7c6df66c622cf389765c7fed775810383",
    "relationship_contribution.py": "6298564273f9d9cbc43d0f6cea22a2f8568506a9",
    "relationship_adapter.py": "c10a26e2f4432a0b7712dbc17e8acca4a76c17c5",
}
CURRENT_INTEGRATION = {
    "main.py": "2573fab44a0daf0fafd05ca14d10be2ce0e0c004",
    "specialist_registry.py": "35eef10d7bf89bffb11d80596d816c8fefd01714",
}

def blob_sha1(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main():
    for rel, expected in {**PROTECTED, **CURRENT_INTEGRATION}.items():
        assert blob_sha1((ROOT / rel).read_bytes()) == expected, rel

    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    shared_source = (ROOT / "shared_intelligence_primitives.py").read_text(encoding="utf-8")
    ast.parse(main_source, filename="main.py")
    ast.parse(shared_source, filename="shared_intelligence_primitives.py")

    fn = next(node for node in ast.parse(main_source).body
             if isinstance(node, ast.FunctionDef) and node.name == "_build_journey_contribution_for_use")
    fn_source = ast.get_source_segment(main_source, fn) or ""
    assert "normalize_journey_contribution" in fn_source
    assert not any(marker in fn_source.casefold() for marker in (
        "pinecone", "groq", "fetch_canonical_context", "_canonical_primary_from_docs",
        "_select_adjacent", "generate", "select canonical",
    ))

    shared_fn = next(node for node in ast.parse(shared_source).body
                     if isinstance(node, ast.FunctionDef) and node.name == "normalize_journey_contribution")
    shared_fn_source = ast.get_source_segment(shared_source, shared_fn) or ""
    assert "JourneyContribution(" in shared_fn_source
    assert not any(marker in shared_fn_source.casefold() for marker in (
        "pinecone", "groq", "fetch_canonical_context", "canonical_primary",
        "routing", "generate",
    ))

    assert "_build_journey_contribution_for_use(body)" in main_source
    assert "journey_contribution.original_question" in main_source
    assert "journey_contribution.journey_synthesis" in main_source
    assert "journey_contribution.journey_ledger" in main_source
    print("v487.94 journey contribution structural QA: PASS")

if __name__ == "__main__":
    main()
