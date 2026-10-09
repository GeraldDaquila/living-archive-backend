"""Single source of truth for protected production-module identity checks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]

PROTECTED_RUNTIME_BLOB_SHAS: Mapping[str, str] = {
    "use_core.py": "fb3208a8d287f16562ffd640d89f65d5e8d18607",
    "specialist_adapters.py": "ca87205fe9634f8bd22b77c5ceca44b0074fb3fa",
    "relationship_contribution.py": "6298564273f9d9cbc43d0f6cea22a2f8568506a9",
    "relationship_adapter.py": "f47b49ce65397d643e96731de3d9e22062fa3e1d",
    "specialist_registry.py": "25964a7ceaa30d7fa9d80524d3e3d5afc7434f0d",
}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def verify_protected_runtime(root: Path = ROOT) -> None:
    """Raise with the exact file when a protected production blob drifts."""
    for relative_path, expected_sha in PROTECTED_RUNTIME_BLOB_SHAS.items():
        actual_sha = git_blob_sha1((root / relative_path).read_bytes())
        if actual_sha != expected_sha:
            raise AssertionError(
                f"Protected runtime blob drift: {relative_path}; "
                f"expected={expected_sha}; actual={actual_sha}"
            )
