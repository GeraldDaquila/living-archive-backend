"""v487.85 structural and seam QA.

Verifies:
- protected core/runtime assets remain unchanged;
- the shared evidence primitive is the only new production dependency;
- the production seam preserves the legacy document mapping shape;
- the seam performs no routing, authority, retrieval, provider, or visitor-prose work.
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

def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main() -> int:
    for rel, expected in PROTECTED.items():
        actual = blob_sha1((ROOT / rel).read_bytes())
        assert actual == expected, (rel, expected, actual)

    for rel in ("main.py", "shared_evidence.py", "shared_intelligence_primitives.py"):
        ast.parse((ROOT / rel).read_text(encoding="utf-8"), filename=rel)

    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    seam_source = (ROOT / "shared_evidence.py").read_text(encoding="utf-8")

    assert "from shared_evidence import" in main_source
    assert "normalize_documents_for_use(parsed, provenance=\"retrieved-context\")" in main_source
    assert "SHARED_EVIDENCE_CONTRACT_VERSION" in main_source
    assert 'APP_VERSION = "v487.85"' in main_source
    assert "from shared_intelligence_primitives import EvidenceItem, normalize_evidence" in seam_source

    forbidden = (
        "groq_client",
        "fetch_canonical_context",
        "pinecone",
        "canonical authority",
        "routing",
        "visitor-facing prose",
        "specialist",
    )
    assert not any(marker in seam_source.casefold() for marker in forbidden)

    for field in ('"id": item.id', '"title": item.title', '"url": item.url', '"text": item.text'):
        assert field in seam_source

    assert "shared_intelligence_primitives" not in (ROOT / "use_core.py").read_text(encoding="utf-8")
    assert "shared_intelligence_primitives" not in (ROOT / "main_v487_28_runtime.py").read_text(encoding="utf-8")
    assert "# v487.85 seam invariant:" in main_source

    print("v487.85 evidence normalization seam QA: PASS")
    print("protected assets: PASS")
    print("shared evidence seam: PASS")
    print("legacy mapping shape preserved: PASS")
    print("orchestration boundaries: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
