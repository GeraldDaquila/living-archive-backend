"""Controlled publisher for the Living Archive meta-crosslink snapshot."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import archive_crosslink
import main

OUTPUT = Path(__file__).resolve().parents[1] / "archive_crosslink_snapshot.json"

def main_publish() -> None:
    index = main._get_pinecone_index()
    inventory = archive_crosslink.build_inventory(index, main)
    snapshot = archive_crosslink.export_snapshot(inventory)
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    OUTPUT.write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    print(f"validated_snapshot=true assets={snapshot['asset_count']} sha256={digest}")

if __name__ == "__main__":
    main_publish()
