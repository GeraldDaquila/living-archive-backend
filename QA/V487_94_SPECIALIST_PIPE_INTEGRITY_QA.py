"""Active specialist-pipe integrity QA.

Protected runtime components remain hash-pinned. The active Guide/USE
integration surface is validated structurally because it advances with the
post-Oct.1 hub architecture.
"""

from pathlib import Path
from protected_runtime_contract import verify_protected_runtime

ROOT = Path(__file__).resolve().parents[1]



def main():
    verify_protected_runtime()

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
