"""Active journey-contribution structural QA."""

from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parents[1]

PROTECTED = {
    "use_core.py": "fb3208a8d287f16562ffd640d89f65d5e8d18607",
    "specialist_adapters.py": "9f253c7ceaeaaba8bd95d2d244015f428fc1285a",
    "relationship_contribution.py": "6298564273f9d9cbc43d0f6cea22a2f8568506a9",
    "relationship_adapter.py": "f47b49ce65397d643e96731de3d9e22062fa3e1d",
    "specialist_registry.py": "25964a7ceaa30d7fa9d80524d3e3d5afc7434f0d",
}

def blob_sha1(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main():
    for rel, expected in PROTECTED.items():
        assert blob_sha1((ROOT / rel).read_bytes()) == expected, rel

    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    shared_source = (ROOT / "shared_intelligence_primitives.py").read_text(encoding="utf-8")
    ast.parse(main_source, filename="main.py")
    ast.parse(shared_source, filename="shared_intelligence_primitives.py")

    tree = ast.parse(main_source)
    fn = next(node for node in tree.body
              if isinstance(node, ast.FunctionDef)
              and node.name == "_build_journey_contribution_for_use")
    fn_source = ast.get_source_segment(main_source, fn) or ""
    assert "normalize_journey_contribution" in fn_source
    assert not any(marker in fn_source.casefold() for marker in (
        "pinecone", "groq", "fetch_canonical_context",
        "_canonical_primary_from_docs", "_select_adjacent",
        "generate", "select canonical",
    ))

    shared_tree = ast.parse(shared_source)
    shared_fn = next(node for node in shared_tree.body
                     if isinstance(node, ast.FunctionDef)
                     and node.name == "normalize_journey_contribution")
    shared_fn_source = ast.get_source_segment(shared_source, shared_fn) or ""
    assert "JourneyContribution(" in shared_fn_source
    assert not any(marker in shared_fn_source.casefold() for marker in (
        "pinecone", "groq", "fetch_canonical_context",
        "canonical_primary", "routing", "generate",
    ))

    assert "_build_journey_contribution_for_use(body)" in main_source
    assert "journey_contribution.original_question" in main_source
    assert "journey_contribution.journey_synthesis" in main_source
    assert "journey_contribution.journey_ledger" in main_source
    assert "route_spoke(" in main_source
    assert "HUB_CONTRACT_DIAGNOSTICS" in main_source

    print("active journey contribution structural QA: PASS")

if __name__ == "__main__":
    main()
