"""Active specialist-pipe integrity QA.

Protected runtime components remain hash-pinned. The active Guide/USE
integration surface is validated structurally because it advances with the
post-Oct.1 hub architecture.
"""

from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]

PROTECTED = {
    "use_core.py": "fb3208a8d287f16562ffd640d89f65d5e8d18607",
    "main_v487_28_runtime.py": "4c8c72d70fa5f93e8bbcdd1c1d8e4696a4949a31",
    "specialist_adapters.py": "ff27c9e7c6df66c622cf389765c7fed775810383",
    "relationship_contribution.py": "6298564273f9d9cbc43d0f6cea22a2f8568506a9",
    "relationship_adapter.py": "c10a26e2f4432a0b7712dbc17e8acca4a76c17c5",
    "specialist_registry.py": "35eef10d7bf89bffb11d80596d816c8fefd01714",
}

def blob_sha1(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main():
    for rel, expected in PROTECTED.items():
        assert blob_sha1((ROOT / rel).read_bytes()) == expected, rel

    for rel in (
        "formation_adapter.py",
        "formation_contribution.py",
        "QA/V487_94_FORMATION_SPECIALIST_QA.py",
        "hub_contracts.py",
    ):
        assert (ROOT / rel).is_file(), rel

    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "FormationAdapter()" in main_source
    assert 'route_id in {"relationship", "formation"}' in main_source
    assert '"FORMATION_HANDOFF"' in main_source
    assert "from hub_contracts import" in main_source
    assert "HUB_CONTRACT_DIAGNOSTICS" in main_source
    assert main_source.count("route_spoke(") >= 2
    assert "EXPECTED_CORE_BLOB_SHA = " in main_source

    hub_source = (ROOT / "hub_contracts.py").read_text(encoding="utf-8")
    assert "def route_spoke(" in hub_source
    assert "expected_specialist_id" in hub_source
    assert "Preserve the full domain contribution" in hub_source

    print("active specialist-pipe integrity QA: PASS")

if __name__ == "__main__":
    main()
