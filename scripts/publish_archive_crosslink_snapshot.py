"""Controlled publisher for the Living Archive meta-crosslink snapshot."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import archive_crosslink
import main

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "archive_crosslink_snapshot.json"
CHECKSUM = ROOT / "archive_crosslink_snapshot.sha256"

def main_publish() -> None:
    api_key = str(__import__('os').getenv('PINECONE_API_KEY') or '').strip()
    index_name = str(__import__('os').getenv('PINECONE_INDEX_NAME') or '').strip()
    if not api_key or not index_name:
        raise RuntimeError('PINECONE_API_KEY and PINECONE_INDEX_NAME must be configured for snapshot publication')
    # The Actions publisher is not a Render process; construct the canonical
    # Pinecone client explicitly instead of relying on runtime-only boot wiring.
    from pinecone import Pinecone
    index = Pinecone(api_key=api_key).Index(index_name)
    if index is None:
        raise RuntimeError('Canonical Pinecone index is unavailable')
    # main supplies canonical access and resource eligibility gates.
    
    inventory = archive_crosslink.build_inventory(index, main)
    snapshot = archive_crosslink.export_snapshot(inventory)
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    OUTPUT.write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    CHECKSUM.write_text(digest + "\\n", encoding="utf-8")
    print(f"validated_snapshot=true assets={snapshot['asset_count']} sha256={digest}")

if __name__ == "__main__":
    main_publish()
