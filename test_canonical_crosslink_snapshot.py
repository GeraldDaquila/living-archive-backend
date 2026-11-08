import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_versioned_crosslink_snapshot_is_the_canonical_runtime_artifact():
    snapshot_path = ROOT / "archive_crosslink_snapshot.json"
    checksum_path = ROOT / "archive_crosslink_snapshot.sha256"

    raw = snapshot_path.read_bytes()
    snapshot = json.loads(raw)

    assert snapshot["contract"] == "archive-crosslink-inventory-v2"
    assert snapshot["source"] == "wordpress-canonical-registry"
    assert snapshot["crosslink_ready"] is True
    assert snapshot["complete"] is True
    assert snapshot["asset_count"] == len(snapshot["assets"])
    assert snapshot["asset_count"] >= 2000

    expected = checksum_path.read_text(encoding="utf-8").strip().split()[0].lower()
    assert expected == hashlib.sha256(raw).hexdigest()


def test_runtime_crosslink_policy_uses_snapshot_and_not_pinecone_inventory():
    source = (ROOT / "archive_crosslink.py").read_text(encoding="utf-8")
    assert "_SNAPSHOT_GITHUB_RAW_URL" in source
    assert "canonical_shared_index_no_monthly_sync" in source
    start = source.index("def start_refresh")
    end = source.index("def _refresh_worker", start)
    assert "index." not in source[start:end]
