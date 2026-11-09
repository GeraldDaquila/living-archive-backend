#!/usr/bin/env python3
"""Read-only USE runtime identity reconciliation for a checked-out Git commit.

The script mirrors main.py::_runtime_source_manifest_sha256 exactly.
It is intentionally stored under scripts/qa so it is excluded from the
application-owned runtime manifest.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "tests", "QA", "scripts", "node_modules",
}


def runtime_source_manifest_sha256() -> tuple[str, int, list[str]]:
    source_files = []
    for path in ROOT.rglob("*.py"):
        if path.is_symlink():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        source_files.append(path)

    source_files.sort(key=lambda item: item.relative_to(ROOT).as_posix())
    digest = hashlib.sha256()
    names = []
    for path in source_files:
        relative_name = path.relative_to(ROOT).as_posix()
        names.append(relative_name)
        digest.update(relative_name.encode("utf-8"))
        digest.update(b"\\0")
        digest.update(path.read_bytes())
        digest.update(b"\\0")
    return digest.hexdigest(), len(source_files), names


def main() -> int:
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    version = re.search(r'^APP_VERSION\\s*=\\s*["\\']([^"\\']+)', main_source, re.M)
    fingerprint = re.search(r'^DEPLOYMENT_FINGERPRINT\\s*=\\s*["\\']([^"\\']+)', main_source, re.M)
    build_id = re.search(r'^CANONICAL_BUILD_ID\\s*=\\s*["\\']([^"\\']+)', main_source, re.M)
    expected_core = re.search(r'^EXPECTED_CORE_BLOB_SHA\\s*=\\s*["\\']([0-9a-f]{40})', main_source, re.M)

    source_sha, count, names = runtime_source_manifest_sha256()
    core_sha = subprocess.check_output(
        ["git", "hash-object", "use_core.py"], cwd=ROOT, text=True
    ).strip()
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()

    report = {
        "commit_sha": commit,
        "app_version": version.group(1) if version else None,
        "deployment_fingerprint": fingerprint.group(1) if fingerprint else None,
        "canonical_build_id": build_id.group(1) if build_id else None,
        "runtime_source_sha256": source_sha,
        "runtime_python_file_count": count,
        "main_py_git_blob_sha": subprocess.check_output(
            ["git", "hash-object", "main.py"], cwd=ROOT, text=True
        ).strip(),
        "expected_protected_core_blob_sha": expected_core.group(1) if expected_core else None,
        "actual_protected_core_blob_sha": core_sha,
        "protected_core_match": bool(expected_core and expected_core.group(1) == core_sha),
        "manifest_paths": names,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["protected_core_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
