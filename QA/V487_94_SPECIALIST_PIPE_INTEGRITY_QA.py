"""v487.94 specialist-pipe integrity QA.

The protected USE core remains immutable. The Guide integration surface and
specialist registry are explicitly versioned here because v487.94 intentionally
changes both to activate the second specialist.
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
}

CURRENT_INTEGRATION = {
    "specialist_registry.py": "35eef10d7bf89bffb11d80596d816c8fefd01714",
}


# main.py is the active Guide integration surface and advances during
# post-Oct.1 architecture work; it is validated structurally below rather
# than pinned to a historical blob hash.


def blob_sha1(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def main():
    for rel, expected in {**PROTECTED, **CURRENT_INTEGRATION}.items():
        assert blob_sha1((ROOT / rel).read_bytes()) == expected, rel

    for rel in (
        "formation_adapter.py",
        "formation_contribution.py",
        "QA/V487_94_FORMATION_SPECIALIST_QA.py",
    ):
        assert (ROOT / rel).is_file(), rel

    registry = (ROOT / "specialist_registry.py").read_text(encoding="utf-8")
    assert 'specialist_id="formation"' in registry
    assert 'status="available"' in registry

    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "FormationAdapter()" in main_source
    assert 'route_id in {"relationship", "formation"}' in main_source
    assert '"FORMATION_HANDOFF"' in main_source
    assert "formation_contract=" in main_source
    assert "from hub_contracts import" in main_source
    assert "route_spoke(" in main_source
    assert "HUB_CONTRACT_DIAGNOSTICS" in main_source
    assert main_source.count("route_spoke(") >= 2
    assert main_source.count("use_core.fetch_canonical_context =") == 1

    print("v487.94 specialist-pipe integrity QA: PASS")


if __name__ == "__main__":
    main()
